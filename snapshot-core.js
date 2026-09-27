// snapshot-core.js
// Shared save logic used by both the popup button and the keyboard-shortcut
// background script, so the two paths can't drift out of sync.
// Depends on `browser` being defined (via webext-compat.js) and must be
// loaded before popup.js / background.js.

function pad(n) {
  return String(n).padStart(2, "0");
}

function localTimestamp(date) {
  return (
    date.getFullYear() +
    "-" + pad(date.getMonth() + 1) +
    "-" + pad(date.getDate()) +
    "T" + pad(date.getHours()) +
    "-" + pad(date.getMinutes()) +
    "-" + pad(date.getSeconds())
  );
}

function buildSnapshotData(tabs, options) {
  const { includeTitles } = options;
  const now = new Date();

  const validTabs = tabs.filter(
    (t) => typeof t.url === "string" && t.url.length > 0
  );
  const entries = validTabs.map((t) =>
    includeTitles ? { url: t.url, title: t.title } : t.url
  );

  const snapshot = {
    savedAt: now.toISOString(), // exact UTC instant
    tabCount: entries.length,
    tabs: entries,
  };

  // One flat folder — the date/time is in the filename and in `savedAt`
  // inside the file, so grouping by date (via analyze_snapshots.py) doesn't
  // need any folder structure to work.
  const filename = `snaptab/snapshot-${localTimestamp(now)}.json`;

  return { snapshot, filename };
}

async function gatherAndSave(options) {
  const queryInfo = options.onlyCurrentWindow ? { currentWindow: true } : {};
  const tabs = await browser.tabs.query(queryInfo);
  const { snapshot, filename } = buildSnapshotData(tabs, options);

  const json = JSON.stringify(snapshot, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const blobUrl = URL.createObjectURL(blob);

  try {
    const downloadId = await browser.downloads.download({
      url: blobUrl,
      filename,
      saveAs: false,
      conflictAction: "uniquify",
    });
    return { downloadId, filename, tabCount: snapshot.tabCount };
  } finally {
    setTimeout(() => URL.revokeObjectURL(blobUrl), 5000);
  }
}
