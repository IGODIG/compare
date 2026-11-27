#!/usr/bin/env python3
"""Build a portable single-file copy from the fast, modular GitHub Pages app."""

from __future__ import annotations

import base64
import json
import mimetypes
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def asset_data_uri(value: str) -> str:
    if not value.startswith("assets/"):
        return value
    path = (ROOT / value).resolve()
    if ROOT.resolve() not in path.parents or not path.is_file():
        raise SystemExit(f"Imagine locală lipsă: {value}")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def inline_local_images(value: object) -> object:
    if isinstance(value, str):
        return asset_data_uri(value)
    if isinstance(value, list):
        return [inline_local_images(item) for item in value]
    if isinstance(value, dict):
        return {key: inline_local_images(item) for key, item in value.items()}
    return value


def main() -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    matching = (ROOT / "matching.mjs").read_text(encoding="utf-8")
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    model_codes = json.loads((ROOT / "data" / "model-codes.json").read_text(encoding="utf-8"))
    fallbacks = json.loads((ROOT / "data" / "image-fallbacks.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "phone-images.json").read_text(encoding="utf-8"))
    evidence = json.loads((ROOT / "data" / "compatibility-evidence.json").read_text(encoding="utf-8"))
    bundles = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in (ROOT / "assets" / "image-bundles").glob("*.json")
    }

    fallbacks = inline_local_images(fallbacks)
    manifest["images"] = {
        uid: {**record, "file": asset_data_uri(record["file"])}
        for uid, record in manifest.get("images", {}).items()
    }
    for font in ("assets/fonts/manrope-latin.woff2", "assets/fonts/manrope-latin-ext.woff2"):
        css = css.replace(f"url('./{font}')", f"url('{asset_data_uri(font)}')")

    app = re.sub(r"^import .*?;\s*", "", app, count=1)
    app = re.sub(r"\bexport\s+(?=function\s)", "", matching) + "\n" + app
    data_init = "const [EMBEDDED_DATA,MODEL_CODES,IMAGE_FALLBACKS,IMAGE_MANIFEST]="
    data_start = app.index(data_init)
    data_end = app.index("\nconst EMBEDDED_BUNDLES", data_start)
    app = app[:data_start] + (
        f"const [EMBEDDED_DATA,MODEL_CODES,IMAGE_FALLBACKS,IMAGE_MANIFEST]="
        f"[{compact(data)},{compact(model_codes)},{compact(fallbacks)},{compact(manifest)}];"
    ) + app[data_end:]
    app = app.replace("const EMBEDDED_BUNDLES={};", f"const EMBEDDED_BUNDLES={compact(bundles)};")

    app = app.replace(
        "loadJSON('./data/compatibility-evidence.json')",
        f"Promise.resolve({compact(evidence)})",
    )
    if any(f"loadJSON('{path}')" in app for path in ('./data.json', './data/model-codes.json', './data/image-fallbacks.json', './data/phone-images.json')):
        raise SystemExit("Nu am putut încorpora toate fișierele JSON în aplicația autonomă.")

    html = re.sub(r'<link rel="stylesheet" href="\./styles\.css">', f"<style>\n{css}\n</style>", html, count=1)
    html = re.sub(r'<link rel="preload" href="\./assets/fonts/[^\"]+" as="font" type="font/woff2" crossorigin>\n?', "", html)
    html = re.sub(r'<script type="module" src="\./app\.js"></script>', lambda _: f"<script type=\"module\">\n{app}\n</script>", html, count=1)
    output = ROOT / "index-complet.html"
    output.write_text(html, encoding="utf-8", newline="\n")
    print(f"Creat {output.name}: {output.stat().st_size:,} bytes.")


if __name__ == "__main__":
    main()
