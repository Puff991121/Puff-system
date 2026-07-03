# 登录接口文档

本文档用于约定 Puff Admin 登录页面与 FastAPI 后端之间的接口、字段及鉴权规则。目前系统只需要预置一个管理员账号。

## 1. 页面功能

登录页面需要支持：

1. 使用账号和密码登录。
2. 登录成功后返回访问令牌，前端保存令牌并进入管理后台。
3. 账号或密码错误时返回明确的错误信息。
4. 后续访问需要鉴权的接口时，通过 Bearer Token 携带访问令牌。

## 2. 基础约定

- 接口前缀：`/api/auth`
- 数据格式：`application/json`
- 字段命名：JSON 使用小写下划线格式
- 令牌类型：Bearer Token
- 编码格式：UTF-8

登录成功后，前端将 `access_token` 保存到浏览器的 `localStorage`，键名为 `access_token`。后续请求统一携带：

```http
Authorization: Bearer <access_token>
```

## 3. 临时管理员账号

目前只需要初始化以下一个账号：

| 字段 | 值 |
| --- | --- |
| username | `Puff` |
| password | `Flt991121` |
| name | `管理员` |
| role | `超级管理员` |
| status | `active` |

账号区分大小写，因此 `Puff` 与 `puff` 不视为同一个账号。

> 安全要求：数据库中不得明文保存密码。后端应使用 `bcrypt`、`Argon2` 等安全算法保存密码哈希；上表中的明文密码仅用于初始化账号和联调。

## 4. 登录接口

```http
POST /api/auth/login
Content-Type: application/json
```

该接口不需要携带访问令牌。

### 4.1 请求字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 是 | 登录账号，去除首尾空格后校验，当前有效值为 `Puff` |
| password | string | 是 | 登录密码，当前有效值为 `Flt991121` |

请求示例：

```json
{
  "username": "Puff",
  "password": "Flt991121"
}
```

### 4.2 字段校验

| 字段 | 校验规则 |
| --- | --- |
| username | 必填，字符串，去除首尾空格后长度为 1～50 个字符，区分大小写 |
| password | 必填，字符串，长度为 1～128 个字符，不自动去除首尾空格，区分大小写 |

请求字段缺失、类型错误或不符合长度规则时，返回 HTTP `422`。

### 4.3 登录成功响应

HTTP 状态码：`200`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| access_token | string | 是 | 后端签发的访问令牌，例如 JWT，有效期建议为 24 小时 |
| token_type | string | 是 | 固定返回小写字符串 `bearer` |

登录接口直接返回以上对象，不使用其他业务接口的 `{ code, message, data }` 包装结构，以匹配当前前端 `src/api/auth.ts` 中的 `LoginResult` 类型。

### 4.4 账号或密码错误

账号不存在、密码错误或账号不可用时，统一返回相同提示，避免泄露账号是否存在。

HTTP 状态码：`401`

```json
{
  "detail": "账号或密码错误"
}
```

响应头建议同时返回：

```http
WWW-Authenticate: Bearer
```

### 4.5 请求参数错误

HTTP 状态码：`422`

```json
{
  "detail": "账号和密码不能为空"
}
```

### 4.6 服务器异常

HTTP 状态码：`500`

```json
{
  "detail": "服务器内部错误"
}
```

后端日志中不得记录明文密码或完整访问令牌。

## 5. Token 最小载荷建议

如果后端使用 JWT，建议至少包含以下载荷：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| sub | string | 用户唯一标识，建议使用数据库用户 ID |
| username | string | 当前登录账号 `Puff` |
| role | string | 当前角色 `超级管理员` |
| iat | integer | 令牌签发时间，Unix 时间戳 |
| exp | integer | 令牌过期时间，Unix 时间戳 |

JWT 载荷不应包含密码、密码哈希或其他敏感信息。

## 6. 鉴权失败约定

访问其他受保护接口时，如果 Token 缺失、无效或已过期，统一返回 HTTP `401`：

```json
{
  "detail": "登录状态已失效，请重新登录"
}
```

前端收到 HTTP `401` 后会删除本地保存的 `access_token`，并跳转到 `/login`。

## 7. 后端实现验收标准

1. 使用 `Puff` 和 `Flt991121` 登录时返回 HTTP `200`，响应中包含 `access_token` 和 `token_type`。
2. 账号大小写错误、密码错误或账号不存在时返回 HTTP `401` 和 `账号或密码错误`。
3. 请求体字段缺失或类型错误时返回 HTTP `422`。
4. 登录接口以外的受保护接口必须校验 `Authorization: Bearer <access_token>`。
5. 无效或过期的 Token 返回 HTTP `401`。
6. 数据库、响应内容和后端日志中均不得出现明文密码。
