# 订单管理接口文档

本文档用于约定订单管理页面与 FastAPI 后端之间的接口、字段及业务规则。

## 1. 页面功能

订单管理页面需要支持：

1. 分页查询和筛选订单。
2. 新增、修改和删除订单。
3. 按日期、关键词、支付方式筛选。
4. 从 Excel 导入订单。
5. 导出 Excel 订单数据。

订单列表字段：

```text
日期、作业要求、模板、格式、学校、价格、支付方式、操作
```

其中“操作”为前端功能列，不需要数据库字段。

## 2. 基础约定

- 接口前缀：`/api/orders`
- 数据格式：`application/json`
- Excel 上传格式：`multipart/form-data`
- 鉴权方式：`Authorization: Bearer <access_token>`
- 日期格式：`YYYY-MM-DD`
- 金额单位：人民币元
- 金额精度：两位小数
- 后端使用 Python `Decimal` 计算金额，MySQL 使用 `DECIMAL(18, 2)` 存储

### 通用 JSON 响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| code | integer | `0` 表示成功，其他值表示业务错误 |
| message | string | 响应说明或错误信息 |
| data | object / array / null | 响应数据 |

## 3. 枚举值

### 3.1 格式 format

只允许以下值，大小写必须一致：

```text
Figma
Psd
Xd
Jsd
Html
定做
无
```

### 3.2 支付方式 payment_method

只允许以下值：

```text
微信
咸鱼
小红书
支付宝
```

## 4. 订单数据模型

### Order

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 数据库主键 |
| order_no | string | 是 | 订单编号，由后端生成，例如 `PF-20260702-018`；当前列表不展示，但可用于搜索和追踪 |
| order_date | string | 是 | 订单日期，格式为 `YYYY-MM-DD` |
| requirement | string | 是 | 作业要求，长度 1～500 个字符 |
| template | string | 是 | 模板名称，长度 1～100 个字符 |
| format | string | 是 | 格式，取值见格式枚举 |
| school | string | 是 | 学校名称，长度 1～100 个字符 |
| price | string | 是 | 价格字符串，固定两位小数，例如 `"299.00"` |
| payment_method | string | 是 | 支付方式，取值见支付方式枚举 |
| created_at | string | 是 | 创建时间，ISO 8601 格式 |
| updated_at | string | 是 | 更新时间，ISO 8601 格式 |

订单中不包含 `status` 状态字段。

示例：

```json
{
  "id": 1,
  "order_no": "PF-20260702-018",
  "order_date": "2026-07-02",
  "requirement": "市场营销课程论文，3000 字，需附数据分析",
  "template": "学术论文标准版",
  "format": "无",
  "school": "复旦大学",
  "price": "299.00",
  "payment_method": "微信",
  "created_at": "2026-07-02T10:42:00+08:00",
  "updated_at": "2026-07-02T10:42:00+08:00"
}
```

## 5. 查询订单列表

```http
GET /api/orders
```

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| page | integer | 否 | 1 | 页码，从 1 开始 |
| page_size | integer | 否 | 10 | 每页数量，范围 1～100 |
| keyword | string | 否 | - | 搜索订单编号、作业要求、模板、格式或学校 |
| payment_method | string | 否 | - | 按支付方式筛选 |
| start_date | string | 否 | - | 开始日期，`YYYY-MM-DD`，包含当天 |
| end_date | string | 否 | - | 结束日期，`YYYY-MM-DD`，包含当天 |
| sort_by | string | 否 | order_date | 排序字段：`order_date`、`price`、`created_at` |
| sort_order | string | 否 | desc | 排序方向：`asc` 或 `desc` |

请求示例：

```http
GET /api/orders?page=1&page_size=10&keyword=论文&payment_method=微信&start_date=2026-07-01&end_date=2026-07-31
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "order_no": "PF-20260702-018",
        "order_date": "2026-07-02",
        "requirement": "市场营销课程论文，3000 字，需附数据分析",
        "template": "学术论文标准版",
        "format": "无",
        "school": "复旦大学",
        "price": "299.00",
        "payment_method": "微信",
        "created_at": "2026-07-02T10:42:00+08:00",
        "updated_at": "2026-07-02T10:42:00+08:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10,
    "total_pages": 1
  }
}
```

## 6. 获取订单详情

```http
GET /api/orders/{order_id}
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "order_no": "PF-20260702-018",
    "order_date": "2026-07-02",
    "requirement": "市场营销课程论文，3000 字，需附数据分析",
    "template": "学术论文标准版",
    "format": "无",
    "school": "复旦大学",
    "price": "299.00",
    "payment_method": "微信",
    "created_at": "2026-07-02T10:42:00+08:00",
    "updated_at": "2026-07-02T10:42:00+08:00"
  }
}
```

## 7. 新增订单

```http
POST /api/orders
```

### 请求体

```json
{
  "order_date": "2026-07-02",
  "requirement": "市场营销课程论文，3000 字，需附数据分析",
  "template": "学术论文标准版",
  "format": "无",
  "school": "复旦大学",
  "price": "299.00",
  "payment_method": "微信"
}
```

### 字段校验

| 字段 | 校验规则 |
| --- | --- |
| order_date | 必填，合法日期，格式为 `YYYY-MM-DD`；未传时也可由后端默认使用当天日期 |
| requirement | 必填，去除首尾空格后长度为 1～500 |
| template | 必填，去除首尾空格后长度为 1～100 |
| format | 必填，只能使用格式枚举值 |
| school | 必填，去除首尾空格后长度为 1～100 |
| price | 必填，大于或等于 `0.01`，最多两位小数 |
| payment_method | 必填，只能使用支付方式枚举值 |

`id`、`order_no`、`created_at` 和 `updated_at` 均由后端生成。

### 成功响应

HTTP 状态码：`201`

```json
{
  "code": 0,
  "message": "订单新增成功",
  "data": {
    "id": 6,
    "order_no": "PF-20260702-019",
    "order_date": "2026-07-02",
    "requirement": "市场营销课程论文，3000 字，需附数据分析",
    "template": "学术论文标准版",
    "format": "无",
    "school": "复旦大学",
    "price": "299.00",
    "payment_method": "微信",
    "created_at": "2026-07-02T15:00:00+08:00",
    "updated_at": "2026-07-02T15:00:00+08:00"
  }
}
```

## 8. 修改订单

```http
PATCH /api/orders/{order_id}
```

请求字段均可选，但至少传入一个字段。

### 请求体

```json
{
  "requirement": "修改后的作业要求",
  "template": "修改后的模板",
  "format": "Figma",
  "school": "浙江大学",
  "price": "399.00",
  "payment_method": "支付宝"
}
```

### 成功响应

```json
{
  "code": 0,
  "message": "订单修改成功",
  "data": {
    "id": 1,
    "order_no": "PF-20260702-018",
    "order_date": "2026-07-02",
    "requirement": "修改后的作业要求",
    "template": "修改后的模板",
    "format": "Figma",
    "school": "浙江大学",
    "price": "399.00",
    "payment_method": "支付宝",
    "created_at": "2026-07-02T10:42:00+08:00",
    "updated_at": "2026-07-02T15:10:00+08:00"
  }
}
```

## 9. 删除订单

```http
DELETE /api/orders/{order_id}
```

### 成功响应

```json
{
  "code": 0,
  "message": "订单删除成功",
  "data": {
    "deleted_id": 1
  }
}
```

## 10. Excel 导入订单

```http
POST /api/orders/import
Content-Type: multipart/form-data
```

### 表单字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | file | 是 | `.xlsx` 文件，最大 5MB |

### Excel 表头

Excel 第一行必须包含以下表头，名称必须一致：

```text
日期、作业要求、模板、格式、学校、价格、支付方式
```

“操作”列不属于数据，不需要出现在 Excel 中。

### Excel 数据校验

- 日期：合法 Excel 日期或 `YYYY-MM-DD` 文本。
- 作业要求、模板、学校：不能为空。
- 格式：必须属于格式枚举。
- 价格：必须为数字且大于或等于 `0.01`。
- 支付方式：必须属于支付方式枚举。
- 空白行忽略。
- 单个文件最多允许 1000 条订单。
- 建议采用“合法行写入、无效行跳过”的部分成功策略。
- 整个导入过程必须使用数据库事务；出现数据库异常时全部回滚。

### 成功或部分成功响应

```json
{
  "code": 0,
  "message": "订单导入完成",
  "data": {
    "total_rows": 5,
    "success_count": 4,
    "failed_count": 1,
    "imported_orders": [
      {
        "id": 10,
        "order_no": "PF-20260702-020",
        "order_date": "2026-07-02",
        "requirement": "网页设计作业",
        "template": "课程设计模板",
        "format": "Html",
        "school": "复旦大学",
        "price": "199.00",
        "payment_method": "微信",
        "created_at": "2026-07-02T15:20:00+08:00",
        "updated_at": "2026-07-02T15:20:00+08:00"
      }
    ],
    "errors": [
      {
        "row": 3,
        "field": "格式",
        "value": "Sketch",
        "message": "格式必须是 Figma、Psd、Xd、Jsd、Html、定做或无"
      }
    ]
  }
}
```

## 11. Excel 导出订单

```http
GET /api/orders/export
```

支持与订单列表相同的筛选参数：

```text
keyword、payment_method、start_date、end_date、sort_by、sort_order
```

### 成功响应

- HTTP 状态码：`200`
- Content-Type：`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition：`attachment; filename="orders-20260702.xlsx"`
- 响应体：Excel 二进制文件

导出的 Excel 表头顺序：

```text
日期、作业要求、模板、格式、学校、价格、支付方式
```

Excel 中日期必须使用日期单元格并设置格式 `yyyy-mm-dd`，价格必须使用数值单元格并设置格式 `0.00`。

## 12. HTTP 状态码

| HTTP 状态码 | 使用场景 |
| --- | --- |
| 200 | 查询、修改、删除、导出或导入完成 |
| 201 | 新增订单成功 |
| 400 | 参数、枚举、日期或金额格式错误 |
| 401 | 未登录或 Token 失效 |
| 403 | 没有订单管理权限 |
| 404 | 订单不存在 |
| 409 | 订单编号冲突或发生并发冲突 |
| 413 | 上传文件超过 5MB |
| 415 | 上传文件不是 `.xlsx` |
| 422 | FastAPI/Pydantic 参数校验失败 |
| 500 | 服务器内部错误 |

错误示例：

```json
{
  "code": 40001,
  "message": "格式必须是 Figma、Psd、Xd、Jsd、Html、定做或无",
  "data": null
}
```

## 13. 推荐数据库设计

表名：`orders`

| 字段 | MySQL 类型 | 约束 |
| --- | --- | --- |
| id | BIGINT UNSIGNED | 主键、自增 |
| user_id | BIGINT UNSIGNED | 非空、索引，所属用户或租户 |
| order_no | VARCHAR(40) | 非空、唯一索引 |
| order_date | DATE | 非空、索引 |
| requirement | VARCHAR(500) | 非空 |
| template | VARCHAR(100) | 非空 |
| format | VARCHAR(20) | 非空 |
| school | VARCHAR(100) | 非空 |
| price | DECIMAL(18, 2) | 非空 |
| payment_method | VARCHAR(20) | 非空 |
| created_at | DATETIME(6) | 非空 |
| updated_at | DATETIME(6) | 非空 |

建议索引：

```sql
UNIQUE KEY uk_orders_order_no (order_no),
KEY idx_orders_user_date (user_id, order_date),
KEY idx_orders_user_payment (user_id, payment_method)
```

## 14. 后端实现要求

1. 金额必须使用 Python `Decimal` 和 MySQL `DECIMAL(18, 2)`。
2. 所有接口只能访问当前登录用户或当前租户的订单。
3. 订单编号必须由后端生成并保证唯一，不能信任前端传入的编号。
4. 新增、修改、删除和导入操作必须使用数据库事务。
5. 列表默认按 `order_date DESC, created_at DESC` 排序。
6. Excel 上传前必须校验扩展名、MIME 类型、文件大小和行数。
7. 不要执行或保存 Excel 中的公式，只读取最终单元格值。
8. 导入错误必须准确返回 Excel 行号、字段、原始值和错误原因。
9. 导出必须复用列表查询的筛选逻辑，避免页面数据和导出结果不一致。
10. 如果支持多人同时修改，建议增加 `version` 字段或使用 `updated_at` 实现乐观锁。
