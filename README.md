# SnapTab — Firefox Extension

Saves a JSON snapshot of every open tab's URL + a timestamp, to your Downloads folder.

## Load it (temporary, for testing)

1. Open `about:debugging#/runtime/this-firefox` in Firefox.
2. Click **Load Temporary Add-on…**
3. Select the `manifest.json` file inside this folder.
4. A toolbar icon appears. Click it, then **Save Snapshot Now** — or use the
   keyboard shortcut `Ctrl+Shift+S`.

This "temporary" load is removed when Firefox restarts. For a permanent
install on your own machine, use `web-ext` to sign/package it (see below),
or package as an unsigned XPI for a self-distributed/enterprise install.

## Output

Each click writes a file to `Downloads/snaptab/snapshot-<local-datetime>.json`:

```json
{
  "savedAt": "2026-09-27T15:13:00.000Z",
  "tabCount": 3,
  "tabs": [
    "https://example.com/",
    "https://developer.mozilla.org/",
    "https://news.ycombinator.com/"
  ]
}
```

Turn on "Include tab titles" in the popup to get `{"url": ..., "title": ...}`
objects instead of bare URL strings.

## Options (in the popup)

- **Include tab titles** — off by default, matches "just URLs + datetime".
- **Current window only** — off by default (captures tabs across all windows).

## Permanent install / packaging

```bash
npm install -g web-ext
cd snaptab
web-ext lint          # sanity check
web-ext build         # produces web-ext-artifacts/snaptab-1.0.0.zip
```

To self-sign for permanent use without the Firefox Add-on Store, use
`web-ext sign` with a free Mozilla API key (addons.mozilla.org →
Developer Hub → Manage API Keys), which returns a signed `.xpi` you can
drag into Firefox to install permanently.

## Analyzing the collection

Once you've got a folder full of snapshots, `analyze_snapshots.py` reads all
of them and groups every URL across the whole collection — no dependencies
beyond Python 3's standard library.

```bash
python3 analyze_snapshots.py <path-to-snaptab-folder> [options]
```

**Flags:**

| Flag | Values | Default | What it does |
|---|---|---|---|
| `--by` | `domain`, `date`, `domain,date`, `date,domain` | `domain` | How to group the tabs. A two-value list nests the second grouping inside the first. |
| `--format` | `text`, `json`, `csv` | `text` | Output shape. `csv` ignores `--by` nesting and just adds `domain`/`date` columns per row. |
| `--out` | a file path | *(stdout)* | Write the report to a file instead of printing it. |
| `--top` | an integer | *(no limit)* | Only show the N largest groups (e.g. the 10 most-visited domains). |

**Examples:**

```bash
# Which domains have you had open the most?
python3 analyze_snapshots.py ~/Downloads/snaptab --by domain --top 15

# What was open on each day?
python3 analyze_snapshots.py ~/Downloads/snaptab --by date

# Both, nested, saved as a file for later
python3 analyze_snapshots.py ~/Downloads/snaptab --by date,domain --format json --out report.json

# Flat spreadsheet-friendly export
python3 analyze_snapshots.py ~/Downloads/snaptab --by domain,date --format csv --out report.csv
```

## Notes

- `savedAt` is UTC ISO 8601; the filename uses your local time for readability.
- Internal pages (`about:*`, `moz-extension:*`) are included if open, since
  they still have a `url`. Remove them by editing the filter in `snapshot-core.js`
  if you don't want them.
- If you were using an earlier build that saved to `Downloads/tab-snapshots/`,
  move those old files into `Downloads/snaptab/` so `analyze_snapshots.py`
  picks them up alongside new ones (it just reads whatever folder you point it at).
