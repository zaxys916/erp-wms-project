# ERP-WMS 后端镜像（FastAPI + Uvicorn）
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 先复制依赖清单，利用 Docker 层缓存，减少反复 pip install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码与迁移脚本
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src

EXPOSE 8000

# 启动前自动执行数据库迁移（幂等），再启动 API
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
