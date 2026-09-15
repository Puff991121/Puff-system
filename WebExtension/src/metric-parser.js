(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.PuffMetricParser = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const METRIC_DEFINITIONS = [
    { key: "followers", label: "粉丝数", aliases: ["粉丝数", "粉丝总数"] },
    { key: "followers_new", label: "新增粉丝", aliases: ["新增粉丝", "涨粉数", "净增粉丝"] },
    { key: "views", label: "观看/阅读", aliases: ["观看量", "阅读量", "播放量", "观看数", "阅读数"] },
    { key: "impressions", label: "曝光量", aliases: ["曝光量", "曝光数", "笔记曝光"] },
    { key: "likes", label: "点赞", aliases: ["点赞量", "点赞数", "获赞数", "点赞"] },
    { key: "collects", label: "收藏", aliases: ["收藏量", "收藏数", "收藏"], excludes: ["获赞与收藏", "赞与收藏"] },
    { key: "comments", label: "评论", aliases: ["评论量", "评论数", "评论"] },
    { key: "shares", label: "分享", aliases: ["分享量", "分享数", "分享"] },
    { key: "interactions", label: "互动量", aliases: ["互动量", "互动数", "互动"] },
    { key: "profile_visits", label: "主页访问", aliases: ["主页访问量", "主页访客", "主页访问"] },
    { key: "notes", label: "笔记数", aliases: ["笔记总数", "笔记数", "发布笔记"] },
    { key: "likes_and_collects", label: "获赞与收藏", aliases: ["获赞与收藏", "赞与收藏"] }
  ];

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function parseCompactNumber(input) {
    if (input === null || input === undefined) return null;
    const clean = String(input).trim().replace(/[,，\s]/g, "");
    const match = clean.match(/(-?\d+(?:\.\d+)?)\s*([万亿wWkK]?)/);
    if (!match) return null;
    const multiplier = { 万: 10000, 亿: 100000000, w: 10000, W: 10000, k: 1000, K: 1000 }[match[2]] || 1;
    return Math.round(Number(match[1]) * multiplier);
  }

  function compactLines(text) {
    return String(text || "")
      .split(/\n+/)
      .map((line) => line.replace(/\s+/g, " ").trim())
      .filter(Boolean)
      .slice(0, 5000);
  }

  function findMetric(lines, definition) {
    for (const alias of definition.aliases) {
      const aliasPattern = escapeRegExp(alias);
      const afterPattern = new RegExp(`${aliasPattern}[^0-9-]{0,12}(-?\\d[\\d,，]*(?:\\.\\d+)?\\s*[万亿wWkK]?)`, "i");
      const beforePattern = new RegExp(`(-?\\d[\\d,，]*(?:\\.\\d+)?\\s*[万亿wWkK]?)\\s*${aliasPattern}`, "i");

      for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index];
        if (!line.includes(alias)) continue;
        if (definition.excludes?.some((phrase) => line.includes(phrase))) continue;

        const beforeMatch = line.match(beforePattern);
        const afterMatch = line.match(afterPattern);
        let inlineMatch = null;

        if (beforeMatch && afterMatch) {
          // 小红书主页头部采用“数值 + 标签”的连续排列，例如：
          // “8 关注数 1608 粉丝数 6858 获赞与收藏”。此时标签两侧都有数字，
          // 应根据整行的起始方向选择前一个数值，而不是误取下一项。
          inlineMatch = /^-?\d/.test(line) ? beforeMatch : afterMatch;
        } else {
          inlineMatch = beforeMatch || afterMatch;
        }

        if (inlineMatch) {
          return { value: parseCompactNumber(inlineMatch[1]), raw: inlineMatch[1], source: line };
        }

        const previousLine = lines[index - 1];
        const nextLine = lines[index + 1];
        const isNumberLine = (value) => value && /^-?\d[\d,，]*(?:\.\d+)?\s*[万亿wWkK]?$/.test(value);
        const previousIsNumber = isNumberLine(previousLine);
        const nextIsNumber = isNumberLine(nextLine);
        let neighborCandidates = [nextLine, previousLine].filter(Boolean);

        if (previousIsNumber && nextIsNumber) {
          // 找到当前连续“标签/数字”序列的起点，以判断页面采用哪种排列方向。
          // 数字起始：8 → 关注数 → 1608 → 粉丝数；标签起始：粉丝数 → 1608。
          let sequenceStart = index;
          while (
            sequenceStart > 0 &&
            Boolean(isNumberLine(lines[sequenceStart - 1])) !== Boolean(isNumberLine(lines[sequenceStart]))
          ) {
            sequenceStart -= 1;
          }
          neighborCandidates = isNumberLine(lines[sequenceStart])
            ? [previousLine, nextLine]
            : [nextLine, previousLine];
        }

        for (const neighbor of neighborCandidates) {
          if (isNumberLine(neighbor)) {
            return { value: parseCompactNumber(neighbor), raw: neighbor, source: `${line} | ${neighbor}` };
          }
        }
      }
    }
    return null;
  }

  function parseText(text) {
    const lines = compactLines(text);
    const metrics = {};
    const evidence = {};

    for (const definition of METRIC_DEFINITIONS) {
      const found = findMetric(lines, definition);
      if (!found || found.value === null) continue;
      metrics[definition.key] = found.value;
      evidence[definition.key] = { label: definition.label, raw: found.raw, source: found.source };
    }

    return { metrics, evidence };
  }

  function collectDocument(documentRef) {
    const bodyText = documentRef.body ? documentRef.body.innerText : "";
    const parsed = parseText(bodyText);
    return {
      schema_version: 1,
      captured_at: new Date().toISOString(),
      page: {
        url: documentRef.location.href,
        title: documentRef.title,
        path: documentRef.location.pathname
      },
      metrics: parsed.metrics,
      evidence: parsed.evidence
    };
  }

  return { METRIC_DEFINITIONS, parseCompactNumber, parseText, collectDocument };
});
