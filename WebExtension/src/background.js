"use strict";

const DEFAULT_SETTINGS = {
  accountName: "账号 1",
  accountId: "account-1",
  endpoint: "",
  accessToken: "",
  autoCollect: false,
  intervalMinutes: 30
};

const CREATOR_URLS = ["https://creator.xiaohongshu.com/*", "https://creator.rednote.com/*"];
const HISTORY_LIMIT = 500;

function storageGet(keys) {
  return chrome.storage.local.get(keys);
}

async function getSettings() {
  const stored = await storageGet("settings");
  return { ...DEFAULT_SETTINGS, ...(stored.settings || {}) };
}

function isCreatorUrl(url = "") {
  try {
    const host = new URL(url).hostname;
    return host === "creator.xiaohongshu.com" || host === "creator.rednote.com";
  } catch {
    return false;
  }
}

function isSafeLocalEndpoint(value) {
  if (!value) return true;
  try {
    const url = new URL(value);
    return ["localhost", "127.0.0.1", "::1"].includes(url.hostname) && ["http:", "https:"].includes(url.protocol);
  } catch {
    return false;
  }
}

async function updateBadge(state, tabId) {
  const states = {
    working: { text: "…", color: "#3c6e71" },
    success: { text: "✓", color: "#2d6a4f" },
    error: { text: "!", color: "#b23a48" }
  };
  const value = states[state];
  if (!value) return;
  await chrome.action.setBadgeText({ text: value.text, tabId });
  await chrome.action.setBadgeBackgroundColor({ color: value.color, tabId });
}

async function saveSnapshot(snapshot) {
  const stored = await storageGet("history");
  const history = Array.isArray(stored.history) ? stored.history : [];
  history.unshift(snapshot);
  await chrome.storage.local.set({
    history: history.slice(0, HISTORY_LIMIT),
    latestSnapshot: snapshot,
    latestStatus: { ok: true, at: snapshot.captured_at, message: "采集完成" }
  });
}

async function sendSnapshot(endpoint, accessToken, snapshot) {
  if (!endpoint) return { skipped: true };
  if (!isSafeLocalEndpoint(endpoint)) throw new Error("接收地址仅允许 localhost 或 127.0.0.1");

  const headers = { "Content-Type": "application/json" };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify(snapshot)
  });
  if (!response.ok) throw new Error(`本地服务返回 HTTP ${response.status}`);
  return { skipped: false };
}

async function collectTab(tab) {
  if (!tab?.id || !isCreatorUrl(tab.url)) {
    throw new Error("请先打开小红书创作服务平台的数据页面");
  }

  await updateBadge("working", tab.id);
  const settings = await getSettings();
  const response = await chrome.tabs.sendMessage(tab.id, { type: "PUFF_COLLECT_PAGE" });
  if (!response?.ok) throw new Error(response?.error || "页面数据读取失败");

  const snapshot = {
    ...response.snapshot,
    account: { id: settings.accountId, name: settings.accountName },
    extension_version: chrome.runtime.getManifest().version
  };

  await saveSnapshot(snapshot);
  let delivery = { skipped: true };
  try {
    delivery = await sendSnapshot(settings.endpoint, settings.accessToken, snapshot);
  } catch (error) {
    await chrome.storage.local.set({
      latestStatus: {
        ok: false,
        at: new Date().toISOString(),
        message: `数据已保存在浏览器；发送失败：${error.message}`
      }
    });
    await updateBadge("error", tab.id);
    return { ok: true, snapshot, delivery: { ok: false, error: error.message } };
  }

  await updateBadge("success", tab.id);
  return { ok: true, snapshot, delivery: { ok: true, ...delivery } };
}

async function configureAlarm() {
  const settings = await getSettings();
  await chrome.alarms.clear("puff-auto-collect");
  if (settings.autoCollect) {
    const periodInMinutes = Math.max(5, Number(settings.intervalMinutes) || 30);
    await chrome.alarms.create("puff-auto-collect", { periodInMinutes });
  }
}

chrome.runtime.onInstalled.addListener(async () => {
  const stored = await storageGet("settings");
  if (!stored.settings) await chrome.storage.local.set({ settings: DEFAULT_SETTINGS, history: [] });
  await configureAlarm();
});

chrome.runtime.onStartup.addListener(configureAlarm);

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "puff-auto-collect") return;
  const tabs = await chrome.tabs.query({ url: CREATOR_URLS });
  for (const tab of tabs) {
    try {
      await collectTab(tab);
    } catch (error) {
      await chrome.storage.local.set({
        latestStatus: { ok: false, at: new Date().toISOString(), message: error.message }
      });
      if (tab.id) await updateBadge("error", tab.id);
    }
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "PUFF_COLLECT_ACTIVE") {
    chrome.tabs.query({ active: true, currentWindow: true })
      .then(([tab]) => collectTab(tab))
      .then(sendResponse)
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message?.type === "PUFF_SETTINGS_UPDATED") {
    configureAlarm()
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  return false;
});
