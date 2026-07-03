# 资产管理接口文档

本文档用于约定资产管理页面与 FastAPI 后端之间的接口和字段。

## 1. 基础约定

- 接口前缀：`/api/assets`
- 数据格式：`application/json`
- 鉴权方式：`Authorization: Bearer <access_token>`
- 金额单位：人民币元
- 金额精度：保留两位小数，后端建议使用 `DECIMAL(18, 2)`，禁止使用浮点类型存储金额
- 资产金额为大于或等于 `0` 的正数
- 负债金额为小于或等于 `0` 的负数
- 净资产计算公式：`总资产 + 总负债`
- 所有时间字段使用 ISO 8601 格式，例如 `2026-07-02T14:30:00+08:00`

### 通用响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| code | integer | 是 | `0` 表示成功，其他值表示业务错误 |
| message | string | 是 | 响应说明或错误信息 |
| data | object / array / null | 是 | 响应数据 |

## 2. 数据模型

### AssetAccount 资产账户

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 账户唯一 ID |
| type | string | 是 | 账户类型：`asset` 资产、`liability` 负债 |
| account | string | 是 | 账户名称，长度 1～30 个字符 |
| amount | string | 是 | 金额字符串，固定两位小数，例如 `"68247.16"`、`"-105.85"` |
| sort_order | integer | 是 | 显示顺序，数字越小越靠前 |
| created_at | string | 是 | 创建时间 |
| updated_at | string | 是 | 最后更新时间 |

示例：

```json
{
  "id": 1,
  "type": "asset",
  "account": "微信",
  "amount": "68247.16",
  "sort_order": 1,
  "created_at": "2026-07-02T10:00:00+08:00",
  "updated_at": "2026-07-02T10:00:00+08:00"
}
```

### AssetSummary 汇总数据

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| total_assets | string | 总资产，所有 `asset` 账户金额之和 |
| total_liabilities | string | 总负债，所有 `liability` 账户金额之和，返回负数 |
| net_assets | string | 净资产：`total_assets + total_liabilities` |
| liability_ratio | string | 负债率百分比：`abs(total_liabilities) / total_assets * 100` |
| asset_account_count | integer | 资产账户数量 |
| liability_account_count | integer | 负债账户数量 |
| updated_at | string | 汇总数据计算时间 |

## 3. 获取资产页面数据

一次性返回账户列表和汇总数据，供资产页面初始化使用。

```http
GET /api/assets
```

### 查询参数

无。

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "summary": {
      "total_assets": "82549.39",
      "total_liabilities": "-905.97",
      "net_assets": "81643.42",
      "liability_ratio": "1.10",
      "asset_account_count": 5,
      "liability_account_count": 5,
      "updated_at": "2026-07-02T14:30:00+08:00"
    },
    "assets": [
      { "id": 1, "type": "asset", "account": "微信", "amount": "68247.16", "sort_order": 1, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 2, "type": "asset", "account": "支付宝", "amount": "2260.64", "sort_order": 2, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 3, "type": "asset", "account": "同花顺", "amount": "8981.59", "sort_order": 3, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 4, "type": "asset", "account": "押金", "amount": "3000.00", "sort_order": 4, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 5, "type": "asset", "account": "银行卡", "amount": "60.00", "sort_order": 5, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" }
    ],
    "liabilities": [
      { "id": 6, "type": "liability", "account": "招商银行", "amount": "-105.85", "sort_order": 1, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 7, "type": "liability", "account": "平安银行", "amount": "-175.70", "sort_order": 2, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 8, "type": "liability", "account": "美团", "amount": "-133.00", "sort_order": 3, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 9, "type": "liability", "account": "京东", "amount": "-306.00", "sort_order": 4, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" },
      { "id": 10, "type": "liability", "account": "花呗", "amount": "-185.42", "sort_order": 5, "created_at": "2026-07-02T10:00:00+08:00", "updated_at": "2026-07-02T10:00:00+08:00" }
    ]
  }
}
```

## 4. 新增账户

```http
POST /api/assets/accounts
```

### 请求体

```json
{
  "type": "asset",
  "account": "新资产账户",
  "amount": "0.00"
}
```

| 字段 | 类型 | 必填 | 校验规则 |
| --- | --- | --- | --- |
| type | string | 是 | 只能为 `asset` 或 `liability` |
| account | string | 是 | 去除首尾空格后长度为 1～30 |
| amount | string | 是 | 最多两位小数；资产不得小于 0，负债不得大于 0 |

### 成功响应

返回新账户和最新汇总数据。

```json
{
  "code": 0,
  "message": "账户新增成功",
  "data": {
    "account": {
      "id": 11,
      "type": "asset",
      "account": "新资产账户",
      "amount": "0.00",
      "sort_order": 6,
      "created_at": "2026-07-02T14:35:00+08:00",
      "updated_at": "2026-07-02T14:35:00+08:00"
    },
    "summary": {
      "total_assets": "82549.39",
      "total_liabilities": "-905.97",
      "net_assets": "81643.42",
      "liability_ratio": "1.10",
      "asset_account_count": 6,
      "liability_account_count": 5,
      "updated_at": "2026-07-02T14:35:00+08:00"
    }
  }
}
```

## 5. 修改账户

用于修改账户名称或金额。前端行内编辑结束后调用。

```http
PATCH /api/assets/accounts/{account_id}
```

### 路径参数

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| account_id | integer | 账户 ID |

### 请求体

字段均为可选，但至少传入一个字段。

```json
{
  "account": "微信零钱",
  "amount": "70000.00"
}
```

| 字段 | 类型 | 必填 | 校验规则 |
| --- | --- | --- | --- |
| account | string | 否 | 去除首尾空格后长度为 1～30 |
| amount | string | 否 | 最多两位小数，正负规则必须与当前账户类型一致 |
| sort_order | integer | 否 | 大于或等于 0 |

### 成功响应

```json
{
  "code": 0,
  "message": "账户更新成功",
  "data": {
    "account": {
      "id": 1,
      "type": "asset",
      "account": "微信零钱",
      "amount": "70000.00",
      "sort_order": 1,
      "created_at": "2026-07-02T10:00:00+08:00",
      "updated_at": "2026-07-02T14:40:00+08:00"
    },
    "summary": {
      "total_assets": "84302.23",
      "total_liabilities": "-905.97",
      "net_assets": "83396.26",
      "liability_ratio": "1.07",
      "asset_account_count": 5,
      "liability_account_count": 5,
      "updated_at": "2026-07-02T14:40:00+08:00"
    }
  }
}
```

## 6. 删除账户

```http
DELETE /api/assets/accounts/{account_id}
```

### 成功响应

```json
{
  "code": 0,
  "message": "账户删除成功",
  "data": {
    "deleted_id": 11,
    "summary": {
      "total_assets": "82549.39",
      "total_liabilities": "-905.97",
      "net_assets": "81643.42",
      "liability_ratio": "1.10",
      "asset_account_count": 5,
      "liability_account_count": 5,
      "updated_at": "2026-07-02T14:45:00+08:00"
    }
  }
}
```

## 7. HTTP 状态码与错误响应

| HTTP 状态码 | 使用场景 |
| --- | --- |
| 200 | 查询、修改或删除成功 |
| 201 | 新增成功 |
| 400 | 参数格式错误或金额正负不符合账户类型 |
| 401 | 未登录或 Token 失效 |
| 403 | 没有资产管理权限 |
| 404 | 账户不存在 |
| 409 | 账户名称重复或数据发生并发冲突 |
| 422 | FastAPI/Pydantic 参数校验失败 |
| 500 | 服务器内部错误 |

错误示例：

```json
{
  "code": 40001,
  "message": "负债账户金额不能大于 0",
  "data": null
}
```

## 8. 后端实现要求

1. 金额计算必须使用 Python `Decimal` 和 MySQL `DECIMAL(18, 2)`。
2. 数据库建议使用一张 `asset_accounts` 表，通过 `type` 区分资产和负债。
3. 汇总数据由后端根据账户数据实时计算，不单独保存，避免数据不一致。
4. 新增、修改、删除接口应在数据库事务中完成。
5. 修改或删除不存在的账户时返回 `404`。
6. 同一用户下建议限制同类型账户名称不能重复；如果允许重复，可删除此约束。
7. 所有接口只能访问当前登录用户或当前租户自己的资产账户。
8. 前端输入金额时会实时计算临时汇总，后端响应返回的汇总数据为最终可信结果。

## 9. 建议的数据库字段

表名：`asset_accounts`

| 字段 | MySQL 类型 | 约束 |
| --- | --- | --- |
| id | BIGINT UNSIGNED | 主键、自增 |
| user_id | BIGINT UNSIGNED | 非空、索引，关联所属用户 |
| type | VARCHAR(20) | 非空，值为 `asset` 或 `liability` |
| account | VARCHAR(30) | 非空 |
| amount | DECIMAL(18, 2) | 非空，默认 `0.00` |
| sort_order | INT UNSIGNED | 非空，默认 `0` |
| created_at | DATETIME(6) | 非空 |
| updated_at | DATETIME(6) | 非空 |

建议唯一索引：

```sql
UNIQUE KEY uk_asset_account_user_type_name (user_id, type, account)
```
