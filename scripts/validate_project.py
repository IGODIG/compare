#!/usr/bin/env python3
"""Validate project JSON, embedded data consistency, and inline JavaScript syntax."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
EMBEDDED_DATA = re.compile(
    r"const EMBEDDED_DATA=(\{.*?\});\s*const EMBEDDED_BUNDLES=",
    flags=re.DOTALL,
)
INLINE_SCRIPT = re.compile(r"<script(?:\s[^>]*)?>(.*?)</script>", flags=re.DOTALL | re.IGNORECASE)


def main() -> None:
    data_path = ROOT / "data.json"
    site_path = ROOT / "index.html"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    if not isinstance(data.get("m"), list) or not data["m"]:
        raise SystemExit("data.json trebuie să conțină o listă m cu modele.")

    html = site_path.read_text(encoding="utf-8")
    embedded_match = EMBEDDED_DATA.search(html)
    if not embedded_match:
        raise SystemExit("Nu am găsit blocul EMBEDDED_DATA în index.html.")
    embedded = json.loads(embedded_match.group(1))
    if embedded != data:
        raise SystemExit("data.json nu corespunde datelor încorporate. Rulează python scripts/sync_embedded_data.py.")

    candidates_path = ROOT / "data" / "new-model-candidates.json"
    if candidates_path.exists():
        candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
        if not isinstance(candidates.get("candidates"), list):
            raise SystemExit("Fișierul de modele-candidat trebuie să conțină o listă candidates.")

    node = shutil.which("node")
    scripts = INLINE_SCRIPT.findall(html)
    if node and scripts:
        with tempfile.TemporaryDirectory(prefix="magnet-validate-") as tmp:
            js_path = Path(tmp) / "inline.js"
            js_path.write_text("\n".join(scripts), encoding="utf-8")
            result = subprocess.run([node, "--check", str(js_path)], capture_output=True, text=True)
            if result.returncode:
                raise SystemExit(result.stderr or "Verificarea sintaxei JavaScript a eșuat.")
    elif not node:
        print("Node.js lipsește; verificarea de sintaxă JavaScript a fost omisă.")

    print(f"OK: {len(data['m'])} înregistrări; JSON și index.html sunt sincronizate.")


if __name__ == "__main__":
    main()
