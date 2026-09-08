"""测试公共工具：登录、认证头、常用资源创建等。"""
from fastapi.testclient import TestClient

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def login(client: TestClient, username: str = ADMIN_USERNAME, password: str = ADMIN_PASSWORD) -> str:
    """登录并返回 access_token。"""
    resp = client.post("/api/auth/token", data={"username": username, "password": password})
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    """构造 Bearer 认证头。"""
    return {"Authorization": f"Bearer {token}"}


def register(client: TestClient, username: str, email: str, password: str = "pass1234") -> dict:
    """注册普通用户并返回响应 JSON。"""
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert resp.status_code == 200, f"注册失败: {resp.text}"
    return resp.json()


def create_warehouse(client: TestClient, token: str, name: str) -> dict:
    resp = client.post("/api/warehouses", json={"name": name}, headers=auth(token))
    assert resp.status_code == 200, f"创建仓库失败: {resp.text}"
    return resp.json()


def create_zone(client: TestClient, token: str, zone_name: str, warehouse_id: int, capacity: int = 100) -> dict:
    resp = client.post(
        "/api/zones",
        json={"zone_name": zone_name, "capacity": capacity, "warehouse_id": warehouse_id},
        headers=auth(token),
    )
    assert resp.status_code == 200, f"创建库位失败: {resp.text}"
    return resp.json()


def create_product(
    client: TestClient,
    token: str,
    name: str,
    sku: str,
    *,
    safety_stock: int = 0,
    price: float = 0,
    cost: float = 0,
) -> dict:
    resp = client.post(
        "/api/products",
        json={"name": name, "sku": sku, "safety_stock": safety_stock, "price": price, "cost": cost},
        headers=auth(token),
    )
    assert resp.status_code == 200, f"创建产品失败: {resp.text}"
    return resp.json()
