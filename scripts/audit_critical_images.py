#!/usr/bin/env python3
"""Check local image coverage for Global Oppo and OnePlus models."""

from __future__ import annotations

import json
import sys
from pathlib import Path


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF", b"GIF8")


def is_image(path: Path) -> bool:
    try:
        return path.is_file() and path.read_bytes()[:12].startswith(IMAGE_SIGNATURES)
    except OSError:
        return False


def main() -> int:
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    bundles = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in (ROOT / "assets" / "image-bundles").glob("*.json")
    }
    manifest_path = ROOT / "data" / "phone-images.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"images": {}}
    fallbacks_path = ROOT / "data" / "image-fallbacks.json"
    extras = json.loads(fallbacks_path.read_text(encoding="utf-8")) if fallbacks_path.exists() else {}
    failures: list[str] = []
    checked = 0

    for model in data["m"]:
        if model[0] not in {"Oppo", "OnePlus"} or model[14] != "Global":
            continue
        checked += 1
        image_id = model[7]
        if isinstance(image_id, int) and image_id >= 0:
            bundle = bundles.get(str(image_id // 50), [])
            if image_id % 50 >= len(bundle) or not bundle[image_id % 50]:
                failures.append(f"{model[0]} {model[1]}: imaginea încorporată {image_id} lipsește")
            continue

        uid = model[19]
        record = manifest.get("images", {}).get(uid, {})
        image = record.get("file") or extras.get(uid)
        image = image[0] if isinstance(image, list) and image else image
        if not isinstance(image, str) or not image.startswith("assets/"):
            failures.append(f"{model[0]} {model[1]}: fotografia nu este salvată local")
            continue
        path = (ROOT / image).resolve()
        if ROOT.resolve() not in path.parents or not is_image(path):
            failures.append(f"{model[0]} {model[1]}: fotografia locală lipsește sau este invalidă ({image})")
            continue

        source = record
        if source.get("file") != image or not source.get("source_url"):
            failures.append(f"{model[0]} {model[1]}: lipsește sursa fotografiei din manifest")

    if failures:
        print("Verificarea imaginilor a găsit probleme:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"OK: {checked} modele Oppo/OnePlus Global au imagine verificată în repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
