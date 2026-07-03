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
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Windows PowerShell 激活命令为：

```powershell
.venv\Scripts\Activate.ps1
```

服务默认地址为 `http://127.0.0.1:8000`。开发环境可访问：

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
| `APP_ADMIN_USERNAME` | 本地演示管理员账号 |
| `APP_ADMIN_PASSWORD` | 本地演示管理员密码 |

生产环境建议使用密钥管理服务注入配置，不要提交 `.env` 文件；设置 `APP_ENV=production` 后，交互式 API 文档会自动关闭。

## 6. 开发命令

```bash
pytest                         # 运行测试
pytest --cov=app               # 查看测试覆盖率
ruff check .                   # 静态检查
ruff format .                  # 格式化代码
```

## 7. 新增业务模块

以订单模块为例：

1. 在 `app/schemas/` 定义输入、输出模型。
2. 在 `app/api/routes/orders.py` 编写接口。
3. 在 `app/api/router.py` 注册路由。
4. 在 `tests/` 添加成功和异常场景测试。
5. 引入数据库后，将业务规则放入 `services/`，数据查询放入 `repositories/`，避免路由层承担过多职责。
