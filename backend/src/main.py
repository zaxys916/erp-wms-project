from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import CORS_ORIGINS
from src.routers import (
    api,
    auth,
    customers,
    inventory,
    movements,
    permission,
    products,
    purchases,
    reports,
    sales,
    stocktake,
    suppliers,
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
app.include_router(suppliers.router, prefix="/api", tags=["供应商管理"])
app.include_router(customers.router, prefix="/api", tags=["客户管理"])
app.include_router(purchases.router, prefix="/api", tags=["采购订单"])
app.include_router(sales.router, prefix="/api", tags=["销售订单"])
app.include_router(reports.router, prefix="/api", tags=["报表统计"])


# ---------- 统一错误响应信封：{code, message, errors?} ----------
def _error_body(code: int, message: str, errors=None) -> dict:
    body = {"code": code, "message": message}
    if errors is not None:
        body["errors"] = errors
    return body


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", []) if part != "body")
        errors.append(f"{loc}: {err.get('msg', '参数不合法')}" if loc else str(err.get("msg", "参数不合法")))
    return JSONResponse(status_code=422, content=_error_body(422, "请求参数校验失败", errors[:10]))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "请求失败"
    return JSONResponse(status_code=exc.status_code, content=_error_body(exc.status_code, message))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # 统一 500 响应，避免泄露内部堆栈
    return JSONResponse(status_code=500, content=_error_body(500, "服务器内部错误，请稍后重试"))


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}


@app.get("/")
def root():
    return {"message": "ERP-WMS API is up and running"}
