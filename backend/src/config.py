import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env（backend/ 的上一级）
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# 默认值与 docker-compose.yml 中 wms-mysql 服务的凭据保持一致
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://wms_user:wms_password@127.0.0.1:3306/wms_db")

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# CORS 白名单：逗号分隔，生产环境务必显式配置，禁止使用 "*"
def _split_list(raw: str):
    return [item.strip() for item in raw.split(",") if item.strip()]


CORS_ORIGINS = _split_list(
    os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080",
    )
)
