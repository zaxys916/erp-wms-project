# ERP-WMS

企业资源计划 + 仓库管理系统（FastAPI + Vue3），覆盖**出入库单据流程、库存台账/流水、盘点与差异跟踪、用户与 RBAC**。

- 后端：FastAPI · SQLAlchemy 2.0 · Pydantic v2 · Alembic · JWT(bcrypt)
- 前端：Vue3 · TypeScript · Element Plus · Pinia · Vite
- 数据：MySQL 8 + Redis 7（Docker Compose）

---

## 功能模块

| 模块 | 说明 | 状态 |
|------|------|------|
| 用户认证 | 注册（强制 `user` 角色）/登录/JWT/当前用户/登出 | ✅ |
| 权限控制 | RBAC：`admin` 全权限、`operator` 业务读写、`user` 只读；权限依赖挂到全部业务路由 | ✅ |
| 仓库与库位 | 仓库 CRUD（仅 admin）；库位 CRUD + 启用/停用 + 容量占用 | ✅ |
| 产品管理 | 产品 CRUD（SKU 唯一、8 位大写校验）；库存以台账聚合为准 | ✅ |
| 出入库单据 | 建单 → **审核生效**（入库增/出库减），可驳回/取消；库存不足审核失败 | ✅ |
| 库存流水 | 每次增减自动落 `inventory_movement`（含行锁，防并发超卖） | ✅ |
| 库存盘点 | 建盘点单（账面快照）→ 录实盘 → 完成自动调账 + 生成差异报告 | ✅ |
| 用户管理 | 用户列表/启停/重置密码（仅 admin） | ✅ |

规划中：采购/销售订单、供应商/客户档案、报表统计、安全库存预警（见 `需求文档.md`）。

---

## 快速开始

### 1. 环境与数据库

```bash
docker compose up -d          # MySQL(:3306) + Redis(:6379)
```

### 2. 后端

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows；Linux/mac: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                             # 建表/迁移
uvicorn src.main:app --reload --port 8000
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173（/api 自动代理到 8000）
```

默认管理员账号：`admin / admin123`（可用 `/api/auth/register` 自助注册普通账号）。

### 4. 运行测试

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests -q     # 13 例，内存 SQLite，无需 MySQL
```

---

## Docker 部署

镜像由 CI 推送至 **GHCR**（`ghcr.io/zaxys916/erp-wms-project-backend` / `-frontend`，私有，需登录拉取）。

```bash
# 方式一：拉取 GHCR 镜像部署
docker login ghcr.io -u <GitHub用户名> -p <PAT>
docker compose --profile app pull
docker compose --profile app up -d
# 访问 http://localhost:8080

# 方式二：本地源码构建
docker compose -f docker-compose.yml -f docker-compose.build.yml --profile app up -d --build
```

> `docker compose up -d` 仍只启动 MySQL/Redis；带 `--profile app` 才会启动前后端。

---

## API 概览（统一前缀 `/api`）

认证（前缀 `/api/auth`）：`POST /token`（OAuth2 表单）· `POST /register` · `GET /users/me` · `POST /logout`

仓库/库位/产品/库存：`/warehouses`、`/zones`(含 `/zones/{id}/enable|disable`)、`/products`、`/inventory`、`GET /inventory/status`、`GET /inventory/movements`

出入库单据：`/movements`（CRUD + `/movements/{id}/approve|reject|cancel`）

盘点/差异：`/stocktakes`（建单/列表/详情）、`PUT /stocktakes/{id}/items/{item_id}`、`POST /stocktakes/{id}/complete`、`GET /stocktakes/discrepancies`

用户/权限：`/users`（admin）、`/permission/roles`、`/permission/me/permissions`

> 业务接口均需 `Authorization: Bearer <token>`。完整列表见 FastAPI 自带的 `/docs`。

---

## 工程化

- **CI**（GitHub Actions，见 `.github/workflows/`）：后端 pytest、前端 type-check/build、PR 镜像构建、master 构建并推送 GHCR、容器冒烟
- **数据库迁移**：Alembic 多版本管理
- **环境变量**：根目录 `.env`（`DATABASE_URL`、`SECRET_KEY`、`CORS_ORIGINS` 逗号分隔白名单）

---

## 目录结构

```
├── docker-compose.yml / docker-compose.build.yml
├── .github/workflows/        # CI + GHCR 发布
├── backend/
│   ├── alembic/              # 迁移版本
│   ├── tests/                # pytest（SQLite 隔离）
│   ├── Dockerfile
│   └── src/
│       ├── main.py           # FastAPI 入口（路由/CORS）
│       ├── models.py         # ORM（10 张表）
│       ├── security.py       # bcrypt + JWT
│       ├── dependencies.py   # 认证与 RBAC 依赖
│       ├── routers/          # 仓库/库位/产品/库存/单据/盘点/用户/认证/权限
│       ├── schemas/          # Pydantic 模型
│       └── services/stock_service.py  # 库存增减 + 流水 + 行锁
└── frontend/
    ├── Dockerfile / nginx.conf
    └── src/
        ├── api/index.ts      # axios 封装（token 拦截/401 跳转）
        ├── router/index.ts   # 路由 + 登录守卫
        └── views/            # 登录/首页/各业务页
```

更多需求与验收标准见 [`需求文档.md`](./需求文档.md)。
