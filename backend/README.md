# Puff 后端项目说明

Puff 后端基于 Python 3.9+ 与 FastAPI，当前提供健康检查、管理员登录、环境配置、自动 API 文档和基础测试，可直接与仓库中的 Vue 前端联调。

## 1. 技术栈

- FastAPI：Web API 框架
- Uvicorn：ASGI 开发服务器
- Pydantic Settings：环境变量配置
- PyJWT：访问令牌生成
- Pytest：自动化测试
- Ruff：代码检查与格式化

## 2. 目录结构

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/          # 各业务路由
│   │   └── router.py        # 路由汇总
│   ├── core/                # 配置、安全等基础能力
│   ├── schemas/             # 请求与响应模型
│   └── main.py              # FastAPI 应用入口
├── tests/                   # 自动化测试
├── .env.example             # 环境变量示例
├── pyproject.toml           # 项目与依赖配置
└── README.md                # 本说明文档
```

后续可按相同方式增加 `models/`、`services/`、`repositories/`，分别放置数据库模型、业务逻辑和数据访问逻辑。

## 3. 本地启动

进入后端目录并创建虚拟环境：

```bash
cd backend
python3 -m venv .venv                  # 创建名为 .venv 的 Python 虚拟环境
source .venv/bin/activate              # 激活虚拟环境，使依赖安装在当前项目内
python -m pip install --upgrade pip     # 将 pip 包管理工具升级到最新版本
python -m pip install -e '.[dev]'       # 以开发模式安装项目及测试、代码检查等开发依赖
cp .env.example .env                   # 复制环境变量模板，生成本地配置文件
uvicorn app.main:app --reload           # 启动后端服务，并在代码修改后自动重启
```

Windows PowerShell 激活命令为：

```powershell
.venv\Scripts\Activate.ps1
```

服务默认地址为 `http://127.0.0.1:8000`。开发环境可访问：

- 服务入口：`http://127.0.0.1:8000/`
- Swagger UI：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`
- 健康检查：`http://127.0.0.1:8000/api/health`

前端默认将 `/api` 代理至该地址，因此前后端同时启动后无需额外修改代理配置。

## 4. 已有接口

### 健康检查

```http
GET /api/health
```

成功响应：

```json
{"status": "ok"}
```

### 管理员登录

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

成功后返回 Bearer Token。初始账号仅用于本地开发，请在 `.env` 中修改；正式用户系统应接入数据库并保存密码哈希，不能沿用此演示账号方案。

### 订单管理

订单接口统一使用 `/api/orders` 前缀，并要求请求头携带登录返回的 Bearer Token：

```text
GET    /api/orders             # 分页、筛选和排序
GET    /api/orders/summary     # 今日、指定日期所在月/年和累计成交统计（可传 reference_date）
GET    /api/orders/{id}        # 订单详情
POST   /api/orders             # 新增订单
PATCH  /api/orders/{id}        # 修改订单
DELETE /api/orders/{id}        # 删除订单
POST   /api/orders/import      # 导入 .xlsx
GET    /api/orders/export      # 导出 .xlsx
```

订单只对所属用户可见，金额以 `Decimal` 处理并使用 MySQL `DECIMAL(18,2)` 保存。完整参数及响应格式以 Swagger 文档和前端的 `orders.md` 约定为准。

### 资产管理

资产接口统一使用 `/api/assets` 前缀，并要求 Bearer Token：

```text
GET    /api/assets                 # 查询账户列表与实时汇总
POST   /api/assets/accounts        # 新增资产或负债账户
PATCH  /api/assets/accounts/{id}   # 修改名称、金额或排序
DELETE /api/assets/accounts/{id}   # 删除账户
```

资产与负债按当前用户隔离，金额使用 `Decimal` 和 MySQL `DECIMAL(18,2)`，净资产与负债率由后端实时计算。

## 5. 环境配置

复制 `.env.example` 为 `.env` 后修改配置。环境变量均使用 `APP_` 前缀：

| 变量 | 作用 |
| --- | --- |
| `APP_NAME` | API 名称 |
| `APP_ENV` | 运行环境：`development`、`test` 或 `production` |
| `APP_DEBUG` | 是否开启调试模式 |
| `APP_SECRET_KEY` | JWT 签名密钥，生产环境必须替换 |
| `APP_ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效分钟数 |
| `APP_CORS_ORIGINS` | 允许跨域的前端地址（JSON 数组） |
| `APP_DATABASE_URL` | MySQL 数据库连接地址 |
| `APP_ADMIN_USERNAME` | 本地演示管理员账号 |
| `APP_ADMIN_PASSWORD` | 本地演示管理员密码 |

生产环境建议使用密钥管理服务注入配置，不要提交 `.env` 文件；设置 `APP_ENV=production` 后，交互式 API 文档会自动关闭。

## 6. 开发命令

```bash
pytest                         # 运行测试
pytest --cov=app               # 查看测试覆盖率
ruff check .                   # 静态检查
ruff format .                  # 格式化代码
alembic upgrade head           # 将数据库表结构升级到最新版
python -m app.scripts.create_admin # 将 .env 中的管理员安全写入 MySQL
```

管理员密码会使用 Argon2 哈希后存入 `users.password_hash`，不会保存明文。初始化脚本可以重复执行；管理员已存在时不会重复写入。

## 7. 新增业务模块

以订单模块为例：

1. 在 `app/schemas/` 定义输入、输出模型。
2. 在 `app/api/routes/orders.py` 编写接口。
3. 在 `app/api/router.py` 注册路由。
4. 在 `tests/` 添加成功和异常场景测试。
5. 引入数据库后，将业务规则放入 `services/`，数据查询放入 `repositories/`，避免路由层承担过多职责。
