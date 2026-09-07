"""仓库/库位/产品基础 CRUD 测试。"""
from helpers import auth, create_product, create_warehouse, create_zone, login


def test_warehouse_crud_flow(client):
    token = login(client)
    headers = auth(token)

    # 创建
    created = create_warehouse(client, token, "华东仓")
    wh_id = created["id"]
    assert created["name"] == "华东仓"

    # 列表包含
    resp = client.get("/api/warehouses", headers=headers)
    assert resp.status_code == 200
    assert any(w["id"] == wh_id for w in resp.json())

    # 详情
    resp = client.get(f"/api/warehouses/{wh_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == wh_id

    # 更新
    resp = client.put(f"/api/warehouses/{wh_id}", json={"name": "华东仓一区"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "华东仓一区"

    # 删除
    resp = client.delete(f"/api/warehouses/{wh_id}", headers=headers)
    assert resp.status_code == 200
    resp = client.get(f"/api/warehouses/{wh_id}", headers=headers)
    assert resp.status_code == 404


def test_zone_crud_and_enable_disable(client):
    token = login(client)
    headers = auth(token)
    warehouse = create_warehouse(client, token, "华南仓")

    zone = create_zone(client, token, "A-01-01", warehouse["id"])
    zone_id = zone["id"]
    assert zone["status"] is True

    # 禁用/启用
    resp = client.put(f"/api/zones/{zone_id}/disable", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] is False

    resp = client.put(f"/api/zones/{zone_id}/enable", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] is True

    # 更新容量
    resp = client.put(
        f"/api/zones/{zone_id}",
        json={"zone_name": "B-02-01", "capacity": 200, "warehouse_id": warehouse["id"]},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["capacity"] == 200

    # 删除
    resp = client.delete(f"/api/zones/{zone_id}", headers=headers)
    assert resp.status_code == 200


def test_product_crud_and_sku_validation(client):
    token = login(client)
    headers = auth(token)

    # SKU 格式校验（8 位大写字母/数字），非法返回 422
    resp = client.post("/api/products", json={"name": "键盘", "sku": "bad-sku"}, headers=headers)
    assert resp.status_code == 422

    product = create_product(client, token, "机械键盘", "TEST0001")
    pid = product["id"]

    # 响应中不应包含冗余 quantity 字段
    assert "quantity" not in product

    resp = client.get(f"/api/products/{pid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "机械键盘"

    resp = client.put(f"/api/products/{pid}", json={"name": "机械键盘 Pro", "sku": "TEST0001"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "机械键盘 Pro"

    resp = client.delete(f"/api/products/{pid}", headers=headers)
    assert resp.status_code == 200
