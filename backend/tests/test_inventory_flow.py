"""出入库单据、库存流水与盘点差异的业务链路测试。"""
from helpers import auth, create_product, create_warehouse, create_zone, login


def _prepare_base(client, token):
    """准备：仓库 + 库位 + 产品，返回 (warehouse, zone, product)。"""
    warehouse = create_warehouse(client, token, "中心仓")
    zone = create_zone(client, token, "A-01-01", warehouse["id"], capacity=500)
    product = create_product(client, token, "机械键盘", "TEST0001")
    return warehouse, zone, product


def _create_order(client, token, order_type, product_id, zone_id, quantity):
    resp = client.post(
        "/api/movements",
        json={
            "order_type": order_type,
            "product_id": product_id,
            "zone_id": zone_id,
            "quantity": quantity,
        },
        headers=auth(token),
    )
    assert resp.status_code == 200, f"创建单据失败: {resp.text}"
    return resp.json()


def test_inbound_outbound_flow_with_movement_ledger(client):
    token = login(client)
    headers = auth(token)
    _, zone, product = _prepare_base(client, token)

    # 入库单 10 → 审核通过
    order = _create_order(client, token, "in", product["id"], zone["id"], 10)
    assert order["status"] == "pending"

    resp = client.post(f"/api/movements/{order['id']}/approve", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    # 库存应 +10
    resp = client.get("/api/inventory", headers=headers)
    inv = [r for r in resp.json() if r["product_id"] == product["id"] and r["zone_id"] == zone["id"]]
    assert len(inv) == 1
    assert inv[0]["quantity"] == 10

    # 库存流水应包含该单据
    resp = client.get("/api/inventory/movements", headers=headers)
    movements = resp.json()
    assert any(m["ref_no"] == order["order_no"] and m["quantity"] == 10 for m in movements)

    # 出库单 4 → 审核通过，库存变 6
    out_order = _create_order(client, token, "out", product["id"], zone["id"], 4)
    resp = client.post(f"/api/movements/{out_order['id']}/approve", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/inventory", headers=headers)
    inv = [r for r in resp.json() if r["product_id"] == product["id"] and r["zone_id"] == zone["id"]]
    assert inv[0]["quantity"] == 6

    # 超量出库 99 → 审核应失败(400 库存不足)，单据保持 pending
    over_order = _create_order(client, token, "out", product["id"], zone["id"], 99)
    resp = client.post(f"/api/movements/{over_order['id']}/approve", headers=headers)
    assert resp.status_code == 400
    assert "库存不足" in resp.json()["detail"]

    # 取消/驳回待审核单据
    resp = client.post(f"/api/movements/{over_order['id']}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_stocktake_complete_generates_discrepancy_and_adjusts(client):
    token = login(client)
    headers = auth(token)
    _, zone, product = _prepare_base(client, token)

    # 先入库 10
    order = _create_order(client, token, "in", product["id"], zone["id"], 10)
    client.post(f"/api/movements/{order['id']}/approve", headers=headers)

    # 创建全仓盘点单 → 账面快照 10
    resp = client.post("/api/stocktakes", json={"remark": "月度盘点"}, headers=headers)
    assert resp.status_code == 200
    stocktake = resp.json()
    assert stocktake["status"] == "pending"
    items = stocktake["items"]
    assert len(items) == 1
    item = items[0]
    assert item["book_qty"] == 10

    # 录入实盘 7 → 差异 -3
    resp = client.put(
        f"/api/stocktakes/{stocktake['id']}/items/{item['id']}",
        json={"actual_qty": 7},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["diff"] == -3

    # 完成盘点 → 调账并生成差异
    resp = client.post(f"/api/stocktakes/{stocktake['id']}/complete", headers=headers)
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["status"] == "completed"
    assert summary["adjusted_count"] == 1
    assert summary["total_diff"] == -3

    # 库存应调整为 7
    resp = client.get("/api/inventory", headers=headers)
    inv = [r for r in resp.json() if r["product_id"] == product["id"] and r["zone_id"] == zone["id"]]
    assert inv[0]["quantity"] == 7

    # 差异报告中应有该记录
    resp = client.get("/api/stocktakes/discrepancies", headers=headers)
    discrepancies = resp.json()
    assert len(discrepancies) == 1
    assert discrepancies[0]["difference"] == -3
    assert discrepancies[0]["status"] == "open"

    # 流水里应有 adjust 记录，ref_no 为盘点单号
    resp = client.get("/api/inventory/movements", headers=headers)
    movements = resp.json()
    assert any(
        m["movement_type"] == "adjust" and m["ref_no"] == summary["order_no"]
        for m in movements
    )

    # 已完成盘点不可再次完成
    resp = client.post(f"/api/stocktakes/{stocktake['id']}/complete", headers=headers)
    assert resp.status_code == 400
