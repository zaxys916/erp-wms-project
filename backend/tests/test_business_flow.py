"""阶段三业务：采购/销售订单闭环 + 库存联动 + 报表 + 安全库存预警。"""
from helpers import auth, create_product, create_warehouse, create_zone, login


def _base_setup(client, token):
    """返回 (zone1, zone2)。"""
    wh = create_warehouse(client, token, "主仓")
    z1 = create_zone(client, token, "A区", wh["id"])
    z2 = create_zone(client, token, "B区", wh["id"])
    return z1, z2


def _create_partner(client, token, path):
    resp = client.post(path, json={"name": "合作方", "contact": "张三", "phone": "138", "address": "某地"}, headers=auth(token))
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_supplier_customer_crud(client):
    token = login(client)
    sup = _create_partner(client, token, "/api/suppliers")
    cus = _create_partner(client, token, "/api/customers")
    assert sup["id"] and cus["id"]

    # 列表分页
    lst = client.get("/api/suppliers", headers=auth(token))
    assert lst.status_code == 200 and lst.json()["items"]
    # 重复名称拒绝
    dup = client.post("/api/suppliers", json={"name": "合作方"}, headers=auth(token))
    assert dup.status_code == 400


def test_purchase_order_approve_receive_updates_stock(client):
    token = login(client)
    z1, z2 = _base_setup(client, token)
    p1 = create_product(client, token, "路由器", "RT789012", safety_stock=10, price=200, cost=120)
    p2 = create_product(client, token, "千兆网线", "WX123456")
    sup = _create_partner(client, token, "/api/suppliers")

    # 创建采购订单（两行明细）
    create = client.post(
        "/api/purchases",
        json={
            "supplier_id": sup["id"],
            "remark": "首批采购",
            "items": [
                {"product_id": p1["id"], "zone_id": z1["id"], "quantity": 50, "unit_price": 100},
                {"product_id": p2["id"], "zone_id": z2["id"], "quantity": 30, "unit_price": 50},
            ],
        },
        headers=auth(token),
    )
    assert create.status_code == 200, create.text
    po = create.json()
    assert po["status"] == "pending"
    assert float(po["total_amount"]) == 50 * 100 + 30 * 50
    assert len(po["items"]) == 2

    po_id = po["id"]

    # 审核后收货
    approve = client.post(f"/api/purchases/{po_id}/approve", headers=auth(token))
    assert approve.status_code == 200 and approve.json()["status"] == "approved"

    receive = client.post(f"/api/purchases/{po_id}/receive", headers=auth(token))
    assert receive.status_code == 200 and receive.json()["status"] == "received"

    # 验证库存已入库
    inv = client.get("/api/inventory", headers=auth(token)).json()["items"]
    qty1 = sum(r["quantity"] for r in inv if r["product_id"] == p1["id"] and r["zone_id"] == z1["id"])
    qty2 = sum(r["quantity"] for r in inv if r["product_id"] == p2["id"] and r["zone_id"] == z2["id"])
    assert qty1 == 50 and qty2 == 30


def test_sales_order_approve_ship_deducts_stock(client):
    token = login(client)
    z1, _ = _base_setup(client, token)
    p1 = create_product(client, token, "路由器", "RT789012")
    sup = _create_partner(client, token, "/api/suppliers")
    cus = _create_partner(client, token, "/api/customers")

    # 先收货 30 个到 A区
    po = client.post(
        "/api/purchases",
        json={"supplier_id": sup["id"], "items": [{"product_id": p1["id"], "zone_id": z1["id"], "quantity": 30, "unit_price": 100}]},
        headers=auth(token),
    ).json()
    client.post(f"/api/purchases/{po['id']}/approve", headers=auth(token))
    client.post(f"/api/purchases/{po['id']}/receive", headers=auth(token))

    # 销售订单发 20 个
    so = client.post(
        "/api/sales",
        json={"customer_id": cus["id"], "items": [{"product_id": p1["id"], "zone_id": z1["id"], "quantity": 20, "unit_price": 200}]},
        headers=auth(token),
    ).json()
    assert so["status"] == "pending"

    client.post(f"/api/sales/{so['id']}/approve", headers=auth(token))
    shipped = client.post(f"/api/sales/{so['id']}/ship", headers=auth(token))
    assert shipped.status_code == 200 and shipped.json()["status"] == "shipped"

    # 验证库存扣减 20
    inv = client.get("/api/inventory", headers=auth(token)).json()["items"]
    qty = sum(r["quantity"] for r in inv if r["product_id"] == p1["id"] and r["zone_id"] == z1["id"])
    assert qty == 10

    # 超发应被负库存拦截
    over = client.post(
        "/api/sales",
        json={"customer_id": cus["id"], "items": [{"product_id": p1["id"], "zone_id": z1["id"], "quantity": 500, "unit_price": 200}]},
        headers=auth(token),
    ).json()
    client.post(f"/api/sales/{over['id']}/approve", headers=auth(token))
    fail = client.post(f"/api/sales/{over['id']}/ship", headers=auth(token))
    assert fail.status_code == 400


def test_stock_alert_below_safety_stock(client):
    token = login(client)
    z1, _ = _base_setup(client, token)
    p = create_product(client, token, "预警品", "YJ998877", safety_stock=10, price=50, cost=30)
    sup = _create_partner(client, token, "/api/suppliers")
    cus = _create_partner(client, token, "/api/customers")

    # 该产品库存为 0，应出现在预警清单
    alerts = client.get("/api/reports/stock-alerts", headers=auth(token)).json()
    hit = [a for a in alerts if a["product_id"] == p["id"]]
    assert hit and hit[0]["total_qty"] == 0 and hit[0]["deficit"] == 10

    # 收货 20 个后，库存高于安全库存，应移出预警
    po = client.post(
        "/api/purchases",
        json={"supplier_id": sup["id"], "items": [{"product_id": p["id"], "zone_id": z1["id"], "quantity": 20, "unit_price": 30}]},
        headers=auth(token),
    ).json()
    client.post(f"/api/purchases/{po['id']}/approve", headers=auth(token))
    client.post(f"/api/purchases/{po['id']}/receive", headers=auth(token))

    alerts_after = client.get("/api/reports/stock-alerts", headers=auth(token)).json()
    assert not [a for a in alerts_after if a["product_id"] == p["id"]]


def test_reports_endpoints(client):
    token = login(client)
    z1, _ = _base_setup(client, token)
    p1 = create_product(client, token, "路由器", "RT789012", price=200, cost=120)
    sup = _create_partner(client, token, "/api/suppliers")
    cus = _create_partner(client, token, "/api/customers")

    po = client.post("/api/purchases", json={"supplier_id": sup["id"], "items": [{"product_id": p1["id"], "zone_id": z1["id"], "quantity": 10, "unit_price": 100}]}, headers=auth(token)).json()
    client.post(f"/api/purchases/{po['id']}/approve", headers=auth(token))
    client.post(f"/api/purchases/{po['id']}/receive", headers=auth(token))

    summary = client.get("/api/reports/inventory-summary", headers=auth(token))
    assert summary.status_code == 200 and summary.json()["total_quantity"] == 10

    trend = client.get("/api/reports/movement-trend", headers=auth(token))
    assert trend.status_code == 200 and trend.json()

    stats = client.get("/api/reports/order-stats", headers=auth(token))
    assert stats.status_code == 200
    purchase = [x for x in stats.json()["purchase"] if x["status"] == "received"]
    assert purchase and purchase[0]["count"] == 1