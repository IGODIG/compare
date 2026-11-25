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
EXTRA_IMAGES = re.compile(r"const EXTRA_IMAGES=(\{.*?\});\s*const bundle=", flags=re.DOTALL)
INLINE_SCRIPT = re.compile(r"<script(?:\s[^>]*)?>(.*?)</script>", flags=re.DOTALL | re.IGNORECASE)


def image_signature(path: Path) -> bool:
    header = path.read_bytes()[:12]
    return header.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF", b"GIF8"))


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

    images_match = EXTRA_IMAGES.search(html)
    if not images_match:
        raise SystemExit("Nu am găsit blocul EXTRA_IMAGES în index.html.")
    extra_images = json.loads(images_match.group(1))
    local_image_count = 0
    for model_id, value in extra_images.items():
        urls = value if isinstance(value, list) else [value]
        for url in urls:
            if not isinstance(url, str) or not url.startswith("assets/"):
                continue
            image_path = (ROOT / url).resolve()
            if ROOT.resolve() not in image_path.parents:
                raise SystemExit(f"Calea imaginii iese din repository: {url}")
            if not image_path.is_file() or not image_signature(image_path):
                raise SystemExit(f"Fotografie locală lipsă sau invalidă pentru modelul {model_id}: {url}")
            local_image_count += 1

    image_manifest_path = ROOT / "data" / "phone-images.json"
    if image_manifest_path.exists():
        image_manifest = json.loads(image_manifest_path.read_text(encoding="utf-8"))
        for model_id, record in image_manifest.get("images", {}).items():
            image_path = ROOT / record.get("file", "")
            if not image_path.is_file() or not record.get("source_url"):
                raise SystemExit(f"Manifest de imagini incomplet pentru modelul {model_id}.")

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

    print(f"OK: {len(data['m'])} înregistrări; JSON și index.html sunt sincronizate; {local_image_count} imagini locale validate.")


if __name__ == "__main__":
    main()
