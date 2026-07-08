# 消费记录接口文档

基础路径：`/api/expenses`。除登录接口外均需请求头 `Authorization: Bearer <token>`。

统一 JSON 响应：`{ "code": 0, "message": "success", "data": ... }`。金额使用两位小数字符串；时间使用 ISO 8601（示例：`2026-07-08T14:30:00+08:00`）。

## 数据结构

| 字段 | 类型 | 约束 |
|---|---|---|
| id | integer | 只读 |
| transaction_time | datetime | 必填，交易时间 |
| transaction_type | string | 必填，1–30 字符，用户自定义 |
| counterparty | string | 必填，1–100 字符 |
| description | string | 必填，1–300 字符 |
| amount | decimal string | 必填，> 0，最多两位小数 |
| payment_method | string | 必填，1–30 字符，用户自定义 |
| created_at / updated_at | datetime | 只读 |

## 接口

- `GET /api/expenses`：分页查询。参数：`page=1`、`page_size=10`、`start_time`、`end_time`、`transaction_type`、`description`（模糊匹配）、`payment_method`、`sort_by=transaction_time|amount|created_at`、`sort_order=asc|desc`。返回 `items/total/page/page_size/total_pages`。
- `GET /api/expenses/summary`：可选参数 `reference_date`，用于返回指定日期所在自然月的消费；未传时使用当前月。返回今日、查询月、本年及累计消费；`month_change_rate` 为查询月相对上月的环比百分比，`year_change_rate` 为本年相对上年的同比百分比。
- `GET /api/expenses/{id}`：查询详情。
- `POST /api/expenses`：新增，Body 为全部可写字段，成功 HTTP 201。
- `PATCH /api/expenses/{id}`：修改，Body 至少包含一个可写字段。
- `DELETE /api/expenses/{id}`：删除，返回 `{ "deleted_id": id }`。
- `GET /api/expenses/export`：参数同列表筛选，返回 `.xlsx` 文件。
- `POST /api/expenses/import`：`multipart/form-data`，字段名 `file`，仅 `.xlsx`，最大 5 MB、1000 行。

Excel 表头顺序固定为：`交易时间、交易类型、交易对方、商品说明、金额、支付方式`。导入结果返回 `total_rows/success_count/failed_count/imported_expenses/errors`；错误项包含 `row/field/value/message`，合法行会正常导入。

常见状态码：`400` 参数或 Excel 内容错误，`401` 未登录，`404` 记录不存在，`413` 文件过大，`415` 文件格式错误，`422` 字段校验失败。
