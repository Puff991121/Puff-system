# Puff 小红书账号监测扩展

一个本地优先的 Manifest V3 浏览器扩展。它读取当前登录的小红书创作服务平台页面中**可见的指标文字**，保存历史快照，并可选发送至本机数据服务。

当前版本：`0.1.1`

## 安装

1. Chrome/Edge 打开扩展管理页，并启用“开发者模式”。
2. 选择“加载已解压的扩展程序”。
3. 选择本目录 `WebExtension`。
4. 在四个浏览器中分别安装一次。
5. 点击扩展图标，在每个浏览器中填写不同的账号名称和账号标识。

Chrome 扩展管理页：`chrome://extensions/`  
Edge 扩展管理页：`edge://extensions/`

## 使用

1. 登录并打开小红书创作服务平台的数据中心或内容分析页面。
2. 点击扩展图标，再点击“采集当前页面”。
3. 结果会保存到当前浏览器的扩展本地存储中。
4. 使用“导出历史”可下载 JSON 文件。

自动采集只会读取**当前已经打开**的创作后台标签页。浏览器关闭、后台页面未打开或登录失效时不会采集。

## 本地接口协议

如需汇总四个浏览器的数据，可填写类似下面的本机接收地址；新安装时该字段默认为空：

```text
POST http://127.0.0.1:8787/api/snapshots
Content-Type: application/json
Authorization: Bearer <可选令牌>
```

请求体示例：

```json
{
  "schema_version": 1,
  "captured_at": "2026-09-10T10:00:00.000Z",
  "account": { "id": "account-1", "name": "美妆号" },
  "page": {
    "url": "https://creator.xiaohongshu.com/...",
    "title": "数据中心",
    "path": "/..."
  },
  "metrics": {
    "followers": 125000,
    "impressions": 3210,
    "collects": 88
  },
  "evidence": {
    "followers": {
      "label": "粉丝数",
      "raw": "12.5万",
      "source": "粉丝数 12.5万"
    }
  },
  "extension_version": "0.1.0"
}
```

将接收地址留空即可完全关闭网络发送。为避免误传账号数据，当前版本只允许 `localhost`、`127.0.0.1` 或 `::1`。

## 已识别指标

- 粉丝数、新增粉丝
- 观看量、阅读量、播放量
- 曝光量
- 点赞、收藏、评论、分享、互动量
- 主页访问量
- 笔记数、获赞与收藏

解析器会保存 `evidence` 字段，记录命中该数值的原始页面文字，便于页面改版后排查误识别。

## 测试

项目无需安装依赖。在安装了 Node.js 的环境运行：

```bash
node --test tests/metric-parser.test.js
```

## 边界

- 扩展不读取或导出 Cookie。
- 扩展不会绕过登录、验证码或平台权限。
- 当前版本读取当前页面渲染出的可见文本，不调用未公开的小红书内部接口。
- 小红书页面结构或指标名称改变时，需要更新 `src/metric-parser.js` 中的指标别名与解析规则。
