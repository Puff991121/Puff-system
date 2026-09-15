(function () {
  "use strict";

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== "PUFF_COLLECT_PAGE") return false;

    try {
      const snapshot = globalThis.PuffMetricParser.collectDocument(document);
      sendResponse({ ok: true, snapshot });
    } catch (error) {
      sendResponse({ ok: false, error: error instanceof Error ? error.message : String(error) });
    }
    return true;
  });
})();
