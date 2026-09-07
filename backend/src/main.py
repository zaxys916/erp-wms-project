from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import CORS_ORIGINS
from src.routers import (
    api,
    auth,
    inventory,
    movements,
    permission,
    products,
    stocktake,
    users,
    zones,
)

app = FastAPI(
    title="ERP-WMS API",
    description="企业资源计划与仓储管理系统API",
    version="1.0.0",
)

# CORS 白名单：默认本地开发地址；生产通过 .env 的 CORS_ORIGINS 显式配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由：业务资源统一挂在 /api 前缀下
app.include_router(api.router, prefix="/api", tags=["仓库管理"])
app.include_router(zones.router, prefix="/api", tags=["库位管理"])
app.include_router(products.router, prefix="/api", tags=["产品管理"])
app.include_router(inventory.router, prefix="/api", tags=["库存管理"])
app.include_router(movements.router, prefix="/api", tags=["出入库单据"])
app.include_router(stocktake.router, prefix="/api", tags=["库存盘点"])
app.include_router(users.router, prefix="/api", tags=["用户管理"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(permission.router, prefix="/api/permission", tags=["权限控制"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}


@app.get("/")
def root():
    return {"message": "ERP-WMS API is up and running"}
