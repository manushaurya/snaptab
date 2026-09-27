// webext-compat.js
// Cross-browser shim: Firefox exposes a promise-based `browser` global.
// Chromium-based browsers only expose callback-based `chrome`. This file
// gives us a single `browser` global either way, so the rest of the code
// doesn't need to care which engine it's running on.
//
// IMPORTANT: this must be loaded via a <script> tag / manifest "scripts"
// entry BEFORE popup.js or background.js — it only works inside an actual
// extension context (the toolbar popup or the background page), not when
// popup.html is opened directly as a file.

if (typeof browser === "undefined") {
  function promisify(fn, thisArg) {
    return (...args) =>
      new Promise((resolve, reject) => {
        fn.call(thisArg, ...args, (result) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else {
            resolve(result);
          }
        });
      });
  }

  var browser = {
    tabs: {
      query: promisify(chrome.tabs.query, chrome.tabs),
    },
    downloads: {
      download: promisify(chrome.downloads.download, chrome.downloads),
    },
    storage: {
      local: {
        get: promisify(chrome.storage.local.get, chrome.storage.local),
        set: promisify(chrome.storage.local.set, chrome.storage.local),
      },
    },
    commands: chrome.commands,
    runtime: chrome.runtime,
  };
}
