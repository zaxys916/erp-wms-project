# ERP-WMS 项目文档

## 1. 项目概述

ERP-WMS（企业资源规划-仓库管理系统）是一个集成的仓库管理解决方案，提供从入库、出库到库存盘点全流程的管理功能。

## 2. 技术栈

### 前端技术

- VUE3 (Vue.TS3)
- ElementPlus (Vue3)

### 后端技术

- FastAPI (ASGI 框架)
- SQLAlchemy (ORM)
- Pydantic (数据验证)

### 数据库

- PostgreSQL

### 其他工具

- Docker
- Redis (用于缓存和会话管理)
- JWT (认证与授权)

## 3. 功能模块

### 核心功能

1. **仓库与库位管理**
   - 库位创建、编辑、删除
   - 库位状态跟踪（可用/占用/维护中）

2. **产品与库存管理**
   - 产品信息管理（SKU、描述、属性）
   - 库存实时监控
   - 库存预警设置

3. **入库与出库流程**
   - 入库单创建与审核
   - 出库单创建与审核
   - 流程状态跟踪

4. **库存盘点功能**
   - 盘点任务创建
   - 实际库存记录
   - 差异分析报告

5. **用户管理**
   - 用户角色分配（管理员/操作员）
   - 权限控制（RBAC）

## 4. API 接口说明

### 基础认证

- `/api/auth/login` - 用户登录
- `/api/auth/logout` - 用户登出
- `/api/users/me` - 获取当前用户信息

### 仓库管理

- `POST /api/zones` - 创建库位
- `GET /api/zones/{id}` - 查询库位详情
- `PUT /api/zones/{id}/enable` - 启用库位
- `PUT /api/zones/{id}/disable` - 禁用库位

### 产品管理

- `POST /api/products` - 创建产品
- `GET /api/products` - 获取所有产品
- `GET /api/products/{id}` - 查询产品详情
- `PUT /api/products/{id}/password` - 更新产品密码

### 库存管理

- `POST /api/inventory/scan` - 扫描库存
- `GET /api/inventory/status` - 获取库存状态
- `POST /api/inventory/discrepancy` - 提交盘点差异

## 5. 数据库设计

### 主要表结构

1. **用户表 (users)**

   ```sql
   id SERIAL PRIMARY KEY,
   username VARCHAR(50) UNIQUE NOT NULL,
   email VARCHAR(100) UNIQUE NOT NULL,
   password_hash VARCHAR(255) NOT NULL,
   is_active BOOLEAN DEFAULT TRUE,
   is_enabled BOOLEAN DEFAULT TRUE,
   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
   updated_at TIMESTAMP WITH TIME ZONE
   ```

2. **库位表 (zones)**

   ```sql
   id SERIAL PRIMARY KEY,
   zone_name VARCHAR(100) NOT NULL,
   capacity INTEGER NOT NULL,
   status BOOLEAN DEFAULT TRUE,  -- 是否启用
   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
   updated_at TIMESTAMP WITH TIME ZONE
   ```

3. **产品表 (products)**

   ```sql
   id SERIAL PRIMARY KEY,
   sku VARCHAR(50) UNIQUE NOT NULL,
   product_name VARCHAR(200) NOT NULL,
   description TEXT,
   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
   updated_at TIMESTAMP WITH TIME ZONE
   ```

4. **库存表 (inventory)**

   ```sql
   id SERIAL PRIMARY KEY,
   product_id INTEGER REFERENCES products(id),
   zone_id INTEGER REFERENCES zones(id),
   quantity INTEGER NOT NULL,
   last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   ```

5. **盘点记录表 (discrepancies)**
   ```sql
   id SERIAL PRIMARY KEY,
   inventory_id INTEGER REFERENCES inventory(id),
   scanned_quantity INTEGER,
   actual_quantity INTEGER,
   difference INTEGER,
   recorded_by INTEGER REFERENCES users(id),
   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   ```

## 6. 安全策略

### 认证机制

- JWT (JSON Web Token) 用于身份验证和授权
- 密码使用 bcrypt 加密存储
- 会话管理通过 Redis 实现

### 权限控制

- 基于角色的访问控制（RBAC）
- 不同角色拥有不同的操作权限
  - 管理员：所有功能
  - 操作员：库存操作、盘点记录查看

## 7. 部署说明

### 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload
```

### 生产环境

- 使用 Docker 容器化部署
- Nginx 作为反向代理
- 配置文件存储在 .env 文件中

## 8. 日志与监控

### 日志系统

- 使用结构化 JSON 格式日志
- 包含请求 ID、时间戳、用户信息等字段
- 支持按级别分类（INFO, WARNING, ERROR）

### 监控指标

- API 响应时间统计
- 错误率分析
- 资源使用情况监控

## 9. 更新日志

### v1.0.0 (初始版本)

- 完成基础功能开发
- 实现用户认证与权限控制
- 添加核心数据模型

### v1.1.0 (后续更新)

- 增加库存盘点功能
- 优化性能和稳定性
- 扩展 API 接口

## 10. 贡献指南

欢迎社区贡献！请遵循以下流程：

1. Fork 项目仓库
2. 创建新分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add new feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 11. 许可证

本项目采用 MIT 许可证。

---

_最后更新：2026年9月7日_
