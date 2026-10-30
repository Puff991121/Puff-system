# 模板管理

菜单位于订单管理下方，页面地址 `/templates`。本模块独立维护模板资料。

## 首版规则

- 模板名称必填，最多 100 个字符，去除首尾空白后在同一用户下唯一。
- 备注选填，最多 1000 个字符。
- 列表与表单按 `Html`（源代码）、`Figma`、`Psd`、`Jsd`（即时设计）、`Xd`、`素材` 排列。素材作为模板附属资料独立保存。
- 每项保存一段完整百度网盘分享文案，最多 2000 个字符。文案包含链接及提取码，不需要分开录入。
- 所有分享项允许缺失，但新增或修改后至少保留一项分享内容。
- 复制时保留完整分享内容；打开时提取百度网盘地址。地址未包含 `pwd` 时，可从文案中的四位提取码补充。
- 查询支持模板名称和备注的模糊搜索、分页，按更新时间从早到晚排列；更新时间相同时按 ID 升序排列。
- 删除前二次确认，仅删除系统中的模板记录。
- 所有数据按当前登录用户隔离，使用与现有模块相同的 Bearer Token 鉴权。

## 接口

所有接口使用现有的 `{code, message, data}` 响应结构。

| 方法 | 地址 | 功能 |
| --- | --- | --- |
| GET | `/api/templates` | 查询，参数 `page`（默认 1）、`page_size`（默认 10，1～100）、`keyword` |
| GET | `/api/templates/{id}` | 查询详情 |
| POST | `/api/templates` | 新增 |
| PATCH | `/api/templates/{id}` | 部分修改，至少传一个字段 |
| DELETE | `/api/templates/{id}` | 删除 |

新增请求示例：

```json
{
  "name": "云肩",
  "notes": "传统文化主题",
  "figma_share": null,
  "psd_share": null,
  "xd_share": null,
  "jsd_share": null,
  "material_share": null,
  "html_share": "通过网盘分享的文件：云肩-源代码 链接: https://pan.baidu.com/s/1y370s39wOHx4sxifc1KNtw?pwd=rsik 提取码: rsik"
}
```

响应增加 `id`、`created_at`、`updated_at` 及 `share_urls`，后者以五种格式名和 `素材` 为键，值为可打开的分享链接或 `null`。`material_share` 保存素材的完整分享文案，历史模板该项默认为 `null`。列表响应包含 `items`、`total`、`page`、`page_size`、`total_pages`。

PATCH 未传字段保留原值，分享内容传 `null` 或空白字符串表示清空。名称冲突返回 `409`，参数错误或清空最后一个分享内容返回 `422`，不存在或属于其他用户的模板返回 `404`。

## 数据库升级

在 `backend` 目录执行 `.venv/bin/alembic upgrade head`。`20261027_07` 新增 `templates` 表，`20261028_09` 在已有表中增加可空的 `material_share` 字段，前置版本为 `20261027_08`，历史模板原有内容保留。
