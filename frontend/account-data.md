# 账号数据接口文档

本文档用于约定账号数据页面与 FastAPI 后端之间的接口、字段和业务规则。

## 1. 页面功能

账号数据页面需要支持：

1. 获取账号列表、动态字段和汇总数据。
2. 新增、修改、删除账号行。
3. 直接修改任意单元格数据。
4. 动态新增和删除自定义字段。
5. 根据账号数据实时计算账号数量、粉丝总数和发布笔记总数。

## 2. 基础约定

- 接口前缀：`/api/account-data`
- 数据格式：`application/json`
- 鉴权方式：`Authorization: Bearer <access_token>`
- 字段命名：JSON 使用小写下划线格式
- 时间格式：ISO 8601，例如 `2026-07-02T14:30:00+08:00`

### 通用响应结构

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

## 3. 数据模型

### 3.1 AccountField 表格字段

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 字段唯一 ID |
| key | string | 是 | 字段唯一标识，创建后不可修改 |
| label | string | 是 | 表头名称，长度 1～20 个字符 |
| type | string | 是 | 字段类型：`text` 或 `number` |
| is_system | boolean | 是 | 是否为系统字段 |
| sort_order | integer | 是 | 显示顺序，数字越小越靠前 |
| created_at | string | 是 | 创建时间 |
| updated_at | string | 是 | 更新时间 |

系统必须预置以下三个字段：

| key | label | type | is_system |
| --- | --- | --- | --- |
| account | 账号 | text | true |
| followers | 粉丝 | number | true |
| notes | 发布笔记数 | number | true |

系统字段不允许删除。

### 3.2 AccountRecord 账号记录

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 账号记录唯一 ID |
| values | object | 是 | 单元格数据，键为字段 `key` |
| sort_order | integer | 是 | 行显示顺序 |
| created_at | string | 是 | 创建时间 |
| updated_at | string | 是 | 更新时间 |

示例：

```json
{
  "id": 1,
  "values": {
    "account": "DW网页设计",
    "followers": 1629,
    "notes": 3,
    "custom_1": "设计类"
  },
  "sort_order": 1,
  "created_at": "2026-07-02T10:00:00+08:00",
  "updated_at": "2026-07-02T10:00:00+08:00"
}
```

### 3.3 AccountDataSummary 汇总数据

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| account_count | integer | 账号数量 |
| total_followers | integer | 所有账号 `followers` 之和 |
| total_notes | integer | 所有账号 `notes` 之和 |
| field_count | integer | 当前字段数量，包括系统字段 |
| updated_at | string | 汇总计算时间 |

## 4. 获取账号数据页面

一次性返回动态字段、账号记录和汇总数据。

```http
GET /api/account-data
```

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "fields": [
      { "id": 1, "key": "account", "label": "账号", "type": "text", "is_system": true, "sort_order": 1, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 2, "key": "followers", "label": "粉丝", "type": "number", "is_system": true, "sort_order": 2, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 3, "key": "notes", "label": "发布笔记数", "type": "number", "is_system": true, "sort_order": 3, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" }
    ],
    "records": [
      { "id": 1, "values": { "account": "DW网页设计", "followers": 1629, "notes": 3 }, "sort_order": 1, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 2, "values": { "account": "了不起的啊点", "followers": 329, "notes": 7 }, "sort_order": 2, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 3, "values": { "account": "阿秋", "followers": 79, "notes": 2 }, "sort_order": 3, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 4, "values": { "account": "爱吃泡芙", "followers": 15, "notes": 3 }, "sort_order": 4, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" }
    ],
    "summary": {
      "account_count": 4,
      "total_followers": 2052,
      "total_notes": 15,
      "field_count": 3,
      "updated_at": "2026-07-02T14:30:00+08:00"
    }
  }
}
```

## 5. 新增账号记录

```http
POST /api/account-data/records
```

### 请求体

```json
{
  "values": {
    "account": "新账号",
    "followers": 0,
    "notes": 0
  }
}
```

### 校验规则

- `account`：必填，字符串，去除首尾空格后长度为 1～100。
- `followers`：非负整数，默认值为 `0`。
- `notes`：非负整数，默认值为 `0`。
- 自定义文本字段默认为空字符串。
- 自定义数字字段默认为 `0`。
- 请求中出现不存在的字段 `key` 时返回 `400`。

### 成功响应

HTTP 状态码：`201`

```json
{
  "code": 0,
  "message": "账号新增成功",
  "data": {
    "record": {
      "id": 5,
      "values": { "account": "新账号", "followers": 0, "notes": 0 },
      "sort_order": 5,
      "created_at": "2026-07-02T14:35:00+08:00",
      "updated_at": "2026-07-02T14:35:00+08:00"
    },
    "summary": {
      "account_count": 5,
      "total_followers": 2052,
      "total_notes": 15,
      "field_count": 3,
      "updated_at": "2026-07-02T14:35:00+08:00"
    }
  }
}
```

## 6. 修改账号记录

用于修改一个或多个单元格。前端单元格编辑完成后调用。

```http
PATCH /api/account-data/records/{record_id}
```

### 请求体

```json
{
  "values": {
    "followers": 1700,
    "notes": 4
  }
}
```

也可以只修改一个单元格：

```json
{
  "values": {
    "followers": 1700
  }
}
```

### 成功响应

```json
{
  "code": 0,
  "message": "账号数据更新成功",
  "data": {
    "record": {
      "id": 1,
      "values": { "account": "DW网页设计", "followers": 1700, "notes": 4 },
      "sort_order": 1,
      "created_at": "2026-07-02T10:00:00+08:00",
      "updated_at": "2026-07-02T14:40:00+08:00"
    },
    "summary": {
      "account_count": 4,
      "total_followers": 2123,
      "total_notes": 16,
      "field_count": 3,
      "updated_at": "2026-07-02T14:40:00+08:00"
    }
  }
}
```

## 7. 删除账号记录

```http
DELETE /api/account-data/records/{record_id}
```

### 成功响应

```json
{
  "code": 0,
  "message": "账号删除成功",
  "data": {
    "deleted_id": 5,
    "summary": {
      "account_count": 4,
      "total_followers": 2052,
      "total_notes": 15,
      "field_count": 3,
      "updated_at": "2026-07-02T14:45:00+08:00"
    }
  }
}
```

## 8. 新增动态字段

```http
POST /api/account-data/fields
```

### 请求体

```json
{
  "label": "获赞数",
  "type": "number"
}
```

| 字段 | 类型 | 必填 | 校验规则 |
| --- | --- | --- | --- |
| label | string | 是 | 去除首尾空格后长度为 1～20；同一用户下不可重复 |
| type | string | 是 | 只能为 `text` 或 `number` |

字段 `key` 由后端生成，建议格式为 `custom_<字段ID>`，前端不得自行指定。

新增字段时，后端需要为已有账号补充默认值：

- `text` 类型默认值为空字符串。
- `number` 类型默认值为 `0`。

### 成功响应

HTTP 状态码：`201`

```json
{
  "code": 0,
  "message": "字段新增成功",
  "data": {
    "field": {
      "id": 4,
      "key": "custom_4",
      "label": "获赞数",
      "type": "number",
      "is_system": false,
      "sort_order": 4,
      "created_at": "2026-07-02T14:50:00+08:00",
      "updated_at": "2026-07-02T14:50:00+08:00"
    },
    "default_value": 0
  }
}
```

## 9. 修改动态字段

用于修改表头名称或字段顺序，不允许修改字段 `key` 和 `type`。

```http
PATCH /api/account-data/fields/{field_id}
```

### 请求体

```json
{
  "label": "累计获赞数",
  "sort_order": 4
}
```

### 成功响应

```json
{
  "code": 0,
  "message": "字段更新成功",
  "data": {
    "field": {
      "id": 4,
      "key": "custom_4",
      "label": "累计获赞数",
      "type": "number",
      "is_system": false,
      "sort_order": 4,
      "created_at": "2026-07-02T14:50:00+08:00",
      "updated_at": "2026-07-02T14:55:00+08:00"
    }
  }
}
```

## 10. 删除动态字段

```http
DELETE /api/account-data/fields/{field_id}
```

### 业务规则

- 系统字段不允许删除，尝试删除时返回 `403`。
- 删除字段时必须同时删除所有账号记录中该字段对应的数据。
- 删除操作不可恢复，必须在数据库事务中完成。

### 成功响应

```json
{
  "code": 0,
  "message": "字段删除成功",
  "data": {
    "deleted_id": 4,
    "deleted_key": "custom_4",
    "summary": {
      "account_count": 4,
      "total_followers": 2052,
      "total_notes": 15,
      "field_count": 3,
      "updated_at": "2026-07-02T15:00:00+08:00"
    }
  }
}
```

## 11. HTTP 状态码

| HTTP 状态码 | 使用场景 |
| --- | --- |
| 200 | 查询、修改或删除成功 |
| 201 | 新增账号或字段成功 |
| 400 | 参数格式错误、字段不存在或值类型错误 |
| 401 | 未登录或 Token 失效 |
| 403 | 没有操作权限或尝试删除系统字段 |
| 404 | 账号记录或字段不存在 |
| 409 | 字段名称重复或发生并发冲突 |
| 422 | FastAPI/Pydantic 参数校验失败 |
| 500 | 服务器内部错误 |

错误示例：

```json
{
  "code": 40001,
  "message": "字段 followers 必须是非负整数",
  "data": null
}
```

## 12. 推荐数据库设计

动态字段可以使用“字段定义表 + 账号记录 JSON”方案。

### account_data_fields

| 字段 | MySQL 类型 | 约束 |
| --- | --- | --- |
| id | BIGINT UNSIGNED | 主键、自增 |
| user_id | BIGINT UNSIGNED | 非空、索引，所属用户或租户 |
| field_key | VARCHAR(50) | 非空 |
| label | VARCHAR(20) | 非空 |
| field_type | VARCHAR(20) | 非空，`text` 或 `number` |
| is_system | BOOLEAN | 非空，默认 `false` |
| sort_order | INT UNSIGNED | 非空，默认 `0` |
| created_at | DATETIME(6) | 非空 |
| updated_at | DATETIME(6) | 非空 |

建议唯一索引：

```sql
UNIQUE KEY uk_account_field_user_key (user_id, field_key),
UNIQUE KEY uk_account_field_user_label (user_id, label)
```

### account_data_records

| 字段 | MySQL 类型 | 约束 |
| --- | --- | --- |
| id | BIGINT UNSIGNED | 主键、自增 |
| user_id | BIGINT UNSIGNED | 非空、索引，所属用户或租户 |
| values_json | JSON | 非空，保存各字段的值 |
| sort_order | INT UNSIGNED | 非空，默认 `0` |
| created_at | DATETIME(6) | 非空 |
| updated_at | DATETIME(6) | 非空 |

## 13. 后端实现要求

1. 后端必须根据字段定义验证 `values` 中每个值的类型。
2. `number` 字段只接受大于或等于 `0` 的整数。
3. 所有读写操作只能访问当前登录用户或当前租户的数据。
4. 新增、修改、删除字段时应使用数据库事务。
5. 删除字段后必须清理已有记录中的对应 JSON 键。
6. 汇总数据由后端实时计算，前端显示以后端返回值为准。
7. `followers` 和 `notes` 系统字段必须始终存在。
8. 建议限制最多 30 个字段、最多 1000 条账号记录，避免表格性能下降。
9. 如果存在多人同时编辑，建议增加 `version` 字段或使用 `updated_at` 做乐观锁。
