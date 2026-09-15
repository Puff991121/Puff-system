"use strict";

const METRIC_LABELS = {
  followers: "粉丝数",
  followers_new: "新增粉丝",
  views: "观看/阅读",
  impressions: "曝光量",
  likes: "点赞",
  collects: "收藏",
  comments: "评论",
  shares: "分享",
  interactions: "互动量",
  profile_visits: "主页访问",
  notes: "笔记数",
  likes_and_collects: "获赞与收藏"
};

const DEFAULT_SETTINGS = {
  accountName: "账号 1",
  accountId: "account-1",
  endpoint: "",
  accessToken: "",
  autoCollect: false,
  intervalMinutes: 30
};

const elements = {
  accountLabel: document.querySelector("#accountLabel"),
  autoBadge: document.querySelector("#autoBadge"),
  collectButton: document.querySelector("#collectButton"),
  status: document.querySelector("#status"),
  connectionDot: document.querySelector("#connectionDot"),
  metricsSection: document.querySelector("#metricsSection"),
  metricsGrid: document.querySelector("#metricsGrid"),
  captureTime: document.querySelector("#captureTime"),
  copyButton: document.querySelector("#copyButton"),
  exportButton: document.querySelector("#exportButton"),
  settingsForm: document.querySelector("#settingsForm")
};

let latestSnapshot = null;

function formatNumber(value) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

function setStatus(message, type = "idle") {
  elements.status.textContent = message;
  elements.status.classList.toggle("error", type === "error");
  elements.connectionDot.className = `connection-dot ${type === "idle" ? "" : type}`;
}

function renderSettings(settings) {
  for (const [key, value] of Object.entries(settings)) {
    const input = document.querySelector(`#${key}`);
    if (!input) continue;
    if (input.type === "checkbox") input.checked = Boolean(value);
    else input.value = value ?? "";
  }
  elements.accountLabel.textContent = settings.accountName;
  elements.autoBadge.textContent = settings.autoCollect ? `每 ${settings.intervalMinutes} 分钟` : "手动采集";
}

function renderSnapshot(snapshot) {
  if (!snapshot) return;
  latestSnapshot = snapshot;
  elements.metricsSection.hidden = false;
  elements.captureTime.textContent = new Date(snapshot.captured_at).toLocaleString("zh-CN", {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit"
  });

  const entries = Object.entries(snapshot.metrics || {});
  elements.metricsGrid.replaceChildren();
  if (!entries.length) {
    const empty = document.createElement("div");
    empty.className = "metric";
    empty.innerHTML = "<span>页面指标</span><strong>未识别</strong>";
    elements.metricsGrid.append(empty);
    return;
  }

  for (const [key, value] of entries) {
    const item = document.createElement("div");
    item.className = "metric";
    const label = document.createElement("span");
    label.textContent = METRIC_LABELS[key] || key;
    const number = document.createElement("strong");
    number.textContent = formatNumber(value);
    item.append(label, number);
    elements.metricsGrid.append(item);
  }
}

async function initialize() {
  const stored = await chrome.storage.local.get(["settings", "latestSnapshot", "latestStatus"]);
  const settings = { ...DEFAULT_SETTINGS, ...(stored.settings || {}) };
  renderSettings(settings);
  renderSnapshot(stored.latestSnapshot);
  if (stored.latestStatus) {
    setStatus(stored.latestStatus.message, stored.latestStatus.ok ? "success" : "error");
  }
}

elements.collectButton.addEventListener("click", async () => {
  elements.collectButton.disabled = true;
  setStatus("正在读取当前页面…");
  try {
    const response = await chrome.runtime.sendMessage({ type: "PUFF_COLLECT_ACTIVE" });
    if (!response?.ok) throw new Error(response?.error || "采集失败");
    renderSnapshot(response.snapshot);
    if (response.delivery?.error) {
      setStatus(`已保存在浏览器；${response.delivery.error}`, "error");
    } else {
      setStatus(response.delivery?.skipped ? "采集完成，已保存在浏览器" : "采集并发送完成", "success");
    }
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    elements.collectButton.disabled = false;
  }
});

elements.settingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(elements.settingsForm);
  const settings = {
    accountName: String(formData.get("accountName") || "").trim(),
    accountId: String(formData.get("accountId") || "").trim(),
    endpoint: String(formData.get("endpoint") || "").trim(),
    accessToken: String(formData.get("accessToken") || ""),
    autoCollect: document.querySelector("#autoCollect").checked,
    intervalMinutes: Math.max(5, Number(formData.get("intervalMinutes")) || 30)
  };

  try {
    if (settings.endpoint) {
      const url = new URL(settings.endpoint);
      if (!["localhost", "127.0.0.1", "::1"].includes(url.hostname)) {
        throw new Error("接收地址必须是 localhost 或 127.0.0.1");
      }
    }
    await chrome.storage.local.set({ settings });
    const result = await chrome.runtime.sendMessage({ type: "PUFF_SETTINGS_UPDATED" });
    if (!result?.ok) throw new Error(result?.error || "配置更新失败");
    renderSettings(settings);
    setStatus("配置已保存到当前浏览器", "success");
  } catch (error) {
    setStatus(error.message, "error");
  }
});

elements.copyButton.addEventListener("click", async () => {
  if (!latestSnapshot) return;
  await navigator.clipboard.writeText(JSON.stringify(latestSnapshot, null, 2));
  setStatus("最新快照已复制", "success");
});

elements.exportButton.addEventListener("click", async () => {
  const { history = [] } = await chrome.storage.local.get("history");
  const blob = new Blob([JSON.stringify(history, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `puff-xhs-history-${new Date().toISOString().slice(0, 10)}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
  setStatus(`已导出 ${history.length} 条快照`, "success");
});

initialize().catch((error) => setStatus(error.message, "error"));
