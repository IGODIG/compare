#!/usr/bin/env python3
"""Copy data.json into the self-contained site's embedded data block."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
HTML_PATH = ROOT / "index.html"
PATTERN = re.compile(
    r"(const EMBEDDED_DATA=)(\{.*?\})(;\s*const EMBEDDED_BUNDLES=)",
    flags=re.DOTALL,
)


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    html = HTML_PATH.read_text(encoding="utf-8")
    replacement = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    updated, count = PATTERN.subn(lambda m: m.group(1) + replacement + m.group(3), html, count=1)
    if count != 1:
        raise SystemExit("Nu am găsit blocul EMBEDDED_DATA în index.html; nu am modificat fișierul.")
    HTML_PATH.write_text(updated, encoding="utf-8", newline="\n")
    print(f"Datele din {DATA_PATH.name} au fost încorporate în {HTML_PATH.name}.")


if __name__ == "__main__":
    main()
