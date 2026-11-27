#!/usr/bin/env python3
"""Validate the static app, stable model references, and local image assets."""

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
UID = re.compile(r"^m_[0-9a-f]{12}$")
IMAGE_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF", b"GIF8")


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"JSON invalid în {path.relative_to(ROOT)}: {error}") from error


def main() -> None:
    data = read_json(ROOT / "data.json")
    if not isinstance(data, dict) or not isinstance(data.get("m"), list) or not data["m"]:
        raise SystemExit("data.json trebuie să conțină o listă nevidă de modele în câmpul m.")
    models = data["m"]
    ids = [model[19] if len(model) > 19 else None for model in models]
    if any(not isinstance(uid, str) or not UID.fullmatch(uid) for uid in ids):
        raise SystemExit("Fiecare model trebuie să aibă un identificator stabil în câmpul 19.")
    if len(set(ids)) != len(ids):
        raise SystemExit("Identificatorii stabili ai modelelor trebuie să fie unici.")
    id_set = set(ids)

    for index, model in enumerate(models):
        for position in (10, 13):
            if len(model) <= position or not isinstance(model[position], list):
                continue
            for relation in model[position]:
                if not isinstance(relation, list) or not relation or relation[0] not in id_set:
                    raise SystemExit(f"Referință de model invalidă în {model[0]} {model[1]}, câmpul {position}.")
                if relation[0] == ids[index]:
                    raise SystemExit(f"Modelul {model[0]} {model[1]} are o relație cu sine însuși.")

    for group in data.get("g", []):
        if not isinstance(group, list) or len(group) < 2 or any(uid not in id_set for uid in group[1]):
            raise SystemExit("Grupul de sticle conține un identificator de model invalid.")

    html_path = ROOT / "index.html"
    html = html_path.read_text(encoding="utf-8")
    for reference in ('href="./styles.css"', 'src="./app.js"', 'href="./favicon.svg"'):
        if reference not in html:
            raise SystemExit(f"index.html nu include resursa necesară: {reference}")

    bundles_dir = ROOT / "assets" / "image-bundles"
    bundles: dict[str, list] = {}
    for path in bundles_dir.glob("*.json"):
        value = read_json(path)
        if not isinstance(value, list):
            raise SystemExit(f"Setul de imagini nu este o listă: {path.relative_to(ROOT)}")
        bundles[path.stem] = value
    for model in models:
        image_id = model[7]
        if isinstance(image_id, int) and image_id >= 0:
            bundle = bundles.get(str(image_id // 50), [])
            if image_id % 50 >= len(bundle) or not bundle[image_id % 50]:
                raise SystemExit(f"Imagine încorporată lipsă pentru {model[0]} {model[1]}.")

    manifest = read_json(ROOT / "data" / "phone-images.json")
    image_records = manifest.get("images", {})
    if any(uid not in id_set for uid in image_records):
        raise SystemExit("Manifestul de imagini conține un identificator de model necunoscut.")
    local_images: set[Path] = set()
    for uid, record in image_records.items():
        image_path = (ROOT / record.get("file", "")).resolve()
        if ROOT.resolve() not in image_path.parents or not image_path.is_file():
            raise SystemExit(f"Imagine locală lipsă pentru {uid}: {record.get('file')}")
        if not image_path.read_bytes()[:12].startswith(IMAGE_SIGNATURES) or not record.get("source_url"):
            raise SystemExit(f"Imagine invalidă sau fără sursă pentru {uid}.")
        local_images.add(image_path)

    fallbacks = read_json(ROOT / "data" / "image-fallbacks.json")
    if any(uid not in id_set for uid in fallbacks):
        raise SystemExit("Maparea imaginilor conține un identificator de model necunoscut.")

    model_codes = read_json(ROOT / "data" / "model-codes.json")
    if any(uid not in id_set or not isinstance(codes, list) or not codes for uid, codes in model_codes.get("models", {}).items()):
        raise SystemExit("Codurile de model conțin un ID invalid sau o listă de coduri goală.")

    evidence = read_json(ROOT / "data" / "compatibility-evidence.json")
    texts, pairs = evidence.get("texts", []), evidence.get("pairs", {})
    for pair, indexes in pairs.items():
        left, right = pair.split(",", 1)
        if left not in id_set or right not in id_set or any(not isinstance(i, int) or i < 0 or i >= len(texts) for i in indexes):
            raise SystemExit("Dovezile de compatibilitate conțin o referință invalidă.")

    candidates_path = ROOT / "data" / "new-model-candidates.json"
    if candidates_path.exists():
        candidates = read_json(candidates_path)
        if not isinstance(candidates.get("candidates"), list):
            raise SystemExit("Fișierul de modele-candidat trebuie să conțină o listă candidates.")

    node = shutil.which("node")
    if node:
        for script in (ROOT / "app.js", ROOT / "matching.mjs"):
            result = subprocess.run([node, "--check", str(script)], capture_output=True, text=True)
            if result.returncode:
                raise SystemExit(result.stderr or f"Sintaxă invalidă în {script.name}.")
    else:
        print("Node.js lipsește; verificarea sintaxei JavaScript a fost omisă.")

    print(f"OK: {len(models)} modele cu ID-uri stabile; relații, dovezi, pagină și {len(local_images)} imagini locale validate.")


if __name__ == "__main__":
    main()
