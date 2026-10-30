# 闲鱼链接管理

菜单位于「模板管理」下方，页面地址 `/xianyu-links`。

## 页面功能与规则

- 新增、修改、删除、分页查询闲鱼链接。
- 闲鱼标题必填，去除首尾空白后最多 200 个字符。
- 闲鱼链接必填，去除首尾空白后最多 2000 个字符。支持商品长链接、分享短链接和完整闲鱼分享文案，不限制内容必须以 HTTP 或 HTTPS 开头。
- 保存和复制时保留完整内容，包括分享口令、说明和换行，不附加单独填写的闲鱼标题。
- 列表从分享文案中提取 HTTP/HTTPS 网址，点击可在新标签页打开；未识别到可用网址时以文本展示，仍可复制。删除前二次确认。
- 搜索匹配标题或链接，按更新时间从早到晚排序，时间相同按 ID 升序排列。
- 每个登录用户只能访问自己的记录，沿用现有 Bearer Token 鉴权。

## 接口

所有接口沿用 `{code, message, data}` 响应结构。

| 方法 | 地址 | 功能 |
| --- | --- | --- |
| GET | `/api/xianyu-links` | 分页搜索，支持 `page`、`page_size`、`keyword` |
| GET | `/api/xianyu-links/{id}` | 查询详情 |
| POST | `/api/xianyu-links` | 新增 |
| PATCH | `/api/xianyu-links/{id}` | 部分修改，至少传一个字段 |
| DELETE | `/api/xianyu-links/{id}` | 删除 |

`page` 从 1 开始，`page_size` 默认 10、范围 1～100；`keyword` 最多 200 个字符。

新增或修改请求示例：

```json
{
  "title": "云肩网页设计模板",
  "link": "【闲鱼】https://m.tb.cn/h.j4M3WAA?tk=rlj8TC9Tio5 CZ001 「我在闲鱼发【网页设计】」\n点击链接直接打开"
}
```

记录响应增加 `id`、`created_at`、`updated_at`。列表响应包含 `items`、`total`、`page`、`page_size`、`total_pages`；删除响应返回 `deleted_id`。

参数错误返回 `422`，未登录返回 `401`，不存在或属于其他用户的记录返回 `404`。

## 数据库升级

在 `backend` 目录执行 `.venv/bin/alembic upgrade head`，新增 `xianyu_links` 表。迁移版本为 `20261027_08`，前置版本为 `20261027_07`。
