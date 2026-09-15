const assert = require("node:assert/strict");
const test = require("node:test");
const parser = require("../src/metric-parser.js");

test("解析中文单位和千分位", () => {
  assert.equal(parser.parseCompactNumber("1.2万"), 12000);
  assert.equal(parser.parseCompactNumber("3,456"), 3456);
  assert.equal(parser.parseCompactNumber("0.8亿"), 80000000);
});

test("解析同一行指标", () => {
  const result = parser.parseText("粉丝数 12.5万\n曝光量 3,210\n收藏数：88");
  assert.deepEqual(result.metrics, { followers: 125000, impressions: 3210, collects: 88 });
});

test("解析标签和值分行的指标", () => {
  const result = parser.parseText("新增粉丝\n128\n主页访问量\n2.4万");
  assert.equal(result.metrics.followers_new, 128);
  assert.equal(result.metrics.profile_visits, 24000);
});

test("不会把复合指标误识别成单项指标", () => {
  const result = parser.parseText("新增粉丝 128\n获赞与收藏 2.1万");
  assert.equal(result.metrics.followers, undefined);
  assert.equal(result.metrics.collects, undefined);
  assert.equal(result.metrics.followers_new, 128);
  assert.equal(result.metrics.likes_and_collects, 21000);
});

test("主页数值在标签前时不会读取下一项指标", () => {
  const result = parser.parseText("8 关注数 1608 粉丝数 6858 获赞与收藏");
  assert.equal(result.metrics.followers, 1608);
  assert.equal(result.metrics.likes_and_collects, 6858);
});

test("主页数值与标签分行时优先读取前一个数值", () => {
  const result = parser.parseText("8\n关注数\n1608\n粉丝数\n6858\n获赞与收藏");
  assert.equal(result.metrics.followers, 1608);
  assert.equal(result.metrics.likes_and_collects, 6858);
});
