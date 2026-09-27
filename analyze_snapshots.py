#!/usr/bin/env python3
"""
analyze_snapshots.py

Reads every snapshot JSON produced by the SnapTab extension (recursively,
from a snaptab/ folder or any folder of similarly-shaped .json files)
and groups all the URLs across the whole collection.

Each input file is expected to look like:
{
  "savedAt": "2026-09-27T15:13:00.000Z",
  "tabCount": 3,
  "tabs": ["https://example.com/", "https://a.b.com/", ...]
}
(entries may also be {"url": ..., "title": ...} objects if you saved with
"Include tab titles" turned on — this script handles both.)

Usage:
    python3 analyze_snapshots.py <path-to-snaptab-folder> [options]

Options:
    --by domain          Group all URLs across all files by domain (default)
    --by date             Group all URLs by the date they were saved
    --by domain,date       Group by date, then by domain within each date
    --format text|json|csv   Output format (default: text)
    --out <file>          Write output to a file instead of stdout
    --top N               Only show the top N domains by tab count (domain grouping only)

Examples:
    python3 analyze_snapshots.py ~/Downloads/snaptab
    python3 analyze_snapshots.py ~/Downloads/snaptab --by date
    python3 analyze_snapshots.py ~/Downloads/snaptab --by domain,date --format json --out report.json
    python3 analyze_snapshots.py ~/Downloads/snaptab --by domain --top 15
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


def get_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc or (parsed.scheme + ":") or "unknown"
    except Exception:
        return "unknown"


def get_date(iso_timestamp: str) -> str:
    # "2026-09-27T15:13:00.000Z" -> "2026-09-27"
    return iso_timestamp.split("T")[0] if iso_timestamp else "unknown-date"


def load_snapshots(root: Path):
    """Yield (file_path, saved_at, url) for every tab in every snapshot file."""
    files = sorted(root.rglob("*.json"))
    if not files:
        print(f"No .json files found under {root}", file=sys.stderr)

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Skipping {f} (couldn't parse: {e})", file=sys.stderr)
            continue

        saved_at = data.get("savedAt", "")
        tabs = data.get("tabs", [])

        # Also handle the (older/optional) domain-grouped shape, just in case.
        if not tabs and isinstance(data.get("domains"), dict):
            tabs = [entry for entries in data["domains"].values() for entry in entries]

        for entry in tabs:
            url = entry["url"] if isinstance(entry, dict) else entry
            if isinstance(url, str) and url:
                yield f, saved_at, url


def group_records(records, by):
    """
    records: iterable of (file_path, saved_at, url)
    by: list like ["domain"], ["date"], or ["date", "domain"]
    Returns a nested dict keyed in the order given by `by`, with leaf values
    being lists of {url, savedAt, file} dicts.
    """
    root = defaultdict(list) if len(by) == 1 else defaultdict(lambda: defaultdict(list))

    for file_path, saved_at, url in records:
        keys = []
        for dim in by:
            if dim == "domain":
                keys.append(get_domain(url))
            elif dim == "date":
                keys.append(get_date(saved_at))

        record = {"url": url, "savedAt": saved_at, "file": str(file_path)}
        if len(keys) == 1:
            root[keys[0]].append(record)
        else:
            root[keys[0]][keys[1]].append(record)

    return root


def print_text(grouped, by, top=None):
    if len(by) == 1:
        items = sorted(grouped.items(), key=lambda kv: -len(kv[1]))
        if top:
            items = items[:top]
        for key, records in items:
            print(f"\n{key}  ({len(records)} tab(s))")
            seen = set()
            for r in records:
                if r["url"] in seen:
                    continue
                seen.add(r["url"])
                print(f"  - {r['url']}  [{r['savedAt']}]")
    else:
        for outer_key in sorted(grouped.keys()):
            inner = grouped[outer_key]
            total = sum(len(v) for v in inner.values())
            print(f"\n=== {outer_key} ({total} tab(s)) ===")
            inner_items = sorted(inner.items(), key=lambda kv: -len(kv[1]))
            if top:
                inner_items = inner_items[:top]
            for inner_key, records in inner_items:
                print(f"  {inner_key}  ({len(records)})")
                seen = set()
                for r in records:
                    if r["url"] in seen:
                        continue
                    seen.add(r["url"])
                    print(f"    - {r['url']}")


def to_plain_dict(grouped):
    if isinstance(grouped, defaultdict):
        return {k: to_plain_dict(v) for k, v in grouped.items()}
    return grouped


def write_json(grouped, out):
    plain = to_plain_dict(grouped)
    text = json.dumps(plain, indent=2, ensure_ascii=False)
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)


def write_csv(records, out, by):
    fieldnames = by + ["url", "savedAt", "file"]
    f = open(out, "w", newline="", encoding="utf-8") if out else sys.stdout
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for file_path, saved_at, url in records:
        row = {"url": url, "savedAt": saved_at, "file": str(file_path)}
        if "domain" in by:
            row["domain"] = get_domain(url)
        if "date" in by:
            row["date"] = get_date(saved_at)
        writer.writerow(row)
    if out:
        f.close()
        print(f"Wrote {out}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("folder", type=Path, help="Path to your snaptab folder")
    parser.add_argument("--by", default="domain", help="domain | date | domain,date | date,domain")
    parser.add_argument("--format", default="text", choices=["text", "json", "csv"])
    parser.add_argument("--out", default=None, help="Write output to this file instead of stdout")
    parser.add_argument("--top", type=int, default=None, help="Only show top N groups by tab count")
    args = parser.parse_args()

    if not args.folder.exists():
        print(f"Folder not found: {args.folder}", file=sys.stderr)
        sys.exit(1)

    by = [b.strip() for b in args.by.split(",") if b.strip() in ("domain", "date")]
    if not by:
        print("--by must contain 'domain', 'date', or both", file=sys.stderr)
        sys.exit(1)

    records = list(load_snapshots(args.folder))
    if not records:
        print("No tabs found in any snapshot file.", file=sys.stderr)
        sys.exit(0)

    if args.format == "csv":
        write_csv(records, args.out, by)
        return

    grouped = group_records(records, by)

    if args.format == "json":
        write_json(grouped, args.out)
    else:
        if args.out:
            import contextlib

            with open(args.out, "w", encoding="utf-8") as f, contextlib.redirect_stdout(f):
                print_text(grouped, by, args.top)
            print(f"Wrote {args.out}")
        else:
            print_text(grouped, by, args.top)


if __name__ == "__main__":
    main()
