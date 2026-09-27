// background.js
// Only handles the keyboard-shortcut path (Ctrl+Shift+S). The popup button
// is self-contained and does not depend on this script — see snapshot-core.js
// for the shared save logic used by both.

const DEFAULT_SETTINGS = {
  includeTitles: false,
  onlyCurrentWindow: false,
};

browser.commands.onCommand.addListener(async (command) => {
  if (command !== "save-snapshot") return;
  try {
    const settings = await browser.storage.local.get(DEFAULT_SETTINGS);
    await gatherAndSave(settings);
  } catch (err) {
    console.error("SnapTab (shortcut) save failed:", err);
  }
});
