// popup.js
const includeTitlesEl = document.getElementById("includeTitles");
const onlyCurrentWindowEl = document.getElementById("onlyCurrentWindow");
const saveBtn = document.getElementById("saveBtn");
const statusEl = document.getElementById("status");

const DEFAULT_SETTINGS = {
  includeTitles: false,
  onlyCurrentWindow: false,
};

async function loadSettings() {
  const stored = await browser.storage.local.get(DEFAULT_SETTINGS);
  includeTitlesEl.checked = stored.includeTitles;
  onlyCurrentWindowEl.checked = stored.onlyCurrentWindow;
}

async function saveSettings() {
  await browser.storage.local.set({
    includeTitles: includeTitlesEl.checked,
    onlyCurrentWindow: onlyCurrentWindowEl.checked,
  });
}

includeTitlesEl.addEventListener("change", saveSettings);
onlyCurrentWindowEl.addEventListener("change", saveSettings);

saveBtn.addEventListener("click", async () => {
  saveBtn.disabled = true;
  statusEl.textContent = "Saving...";
  try {
    const result = await gatherAndSave({
      includeTitles: includeTitlesEl.checked,
      onlyCurrentWindow: onlyCurrentWindowEl.checked,
    });
    statusEl.textContent = `Saved ${result.tabCount} tab(s) to Downloads/${result.filename}`;
  } catch (err) {
    console.error("SnapTab save failed:", err);
    statusEl.textContent = `Failed: ${err.message || err}`;
  } finally {
    saveBtn.disabled = false;
  }
});

loadSettings();
