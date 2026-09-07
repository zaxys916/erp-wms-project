"""认证与 RBAC 相关测试。"""
from helpers import ADMIN_PASSWORD, auth, login, register


def test_anonymous_access_business_api_returns_401(client):
    """未登录访问业务接口应被拦截。"""
    resp = client.get("/api/warehouses")
    assert resp.status_code == 401


def test_login_with_wrong_password_returns_401(client):
    resp = client.post("/api/auth/token", data={"username": "admin", "password": "wrong-password"})
    assert resp.status_code == 401


def test_admin_login_and_me(client):
    token = login(client)
    resp = client.get("/api/auth/users/me", headers=auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"


def test_register_forces_user_role(client):
    """注册接口应强制普通 user 角色，禁止自建管理员。"""
    body = register(client, "alice", "alice@wms.dev")
    assert body["role"] == "user"
    token = login(client, "alice", "pass1234")
    assert token


def test_normal_user_cannot_manage_users(client):
    """普通 user 无 user:manage 权限，访问用户管理应 403。"""
    register(client, "alice", "alice@wms.dev")
    token = login(client, "alice", "pass1234")

    resp = client.get("/api/users", headers=auth(token))
    assert resp.status_code == 403


def test_normal_user_can_read_zones(client):
    """普通 user 拥有只读权限，可读取库位。"""
    register(client, "alice", "alice@wms.dev")
    token = login(client, "alice", "pass1234")

    resp = client.get("/api/zones", headers=auth(token))
    assert resp.status_code == 200


def test_normal_user_cannot_write_product(client):
    """普通 user 无写入权限，创建产品应 403。"""
    register(client, "alice", "alice@wms.dev")
    token = login(client, "alice", "pass1234")

    resp = client.post(
        "/api/products",
        json={"name": "键盘", "sku": "ABCD1234"},
        headers=auth(token),
    )
    assert resp.status_code == 403


def test_admin_can_list_users(client):
    token = login(client)
    resp = client.get("/api/users", headers=auth(token))
    assert resp.status_code == 200
    names = [u["username"] for u in resp.json()]
    assert "admin" in names
