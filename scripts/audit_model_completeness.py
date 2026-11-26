#!/usr/bin/env python3
"""Build a compact monthly report for incomplete Global/Europe phone records."""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def read_assignment(html: str, marker: str) -> object:
    start = html.find(marker)
    if start < 0:
        raise ValueError(f"Nu am găsit declarația {marker!r} în index.html.")
    decoder = json.JSONDecoder()
    value, _ = decoder.raw_decode(html[start + len(marker) :].lstrip())
    return value


def display_name(model: list[object]) -> str:
    film = model[17] == "film" if len(model) > 17 else False
    if film:
        panel = model[18] if len(model) > 18 else ""
        return f"{model[0]} {model[1]} ({panel})"
    return f"{model[0]} {model[1]}"


def image_status(index: int, model: list[object], bundles: dict, extras: dict) -> str:
    image_id = model[7]
    if isinstance(image_id, int) and image_id >= 0:
        images = bundles.get(str(image_id // 50), [])
        return "încorporată" if image_id % 50 < len(images) and images[image_id % 50] else "lipsă"

    image = extras.get(str(index))
    images = image if isinstance(image, list) else [image]
    for candidate in images:
        if not isinstance(candidate, str):
            continue
        if candidate.startswith(("https://", "http://")):
            return "externă"
        if candidate.startswith("assets/"):
            path = (ROOT / candidate).resolve()
            if ROOT.resolve() in path.parents and path.is_file():
                return "locală"
    return "lipsă"


def main() -> None:
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    bundles = read_assignment(html, "const EMBEDDED_BUNDLES=")
    extras = read_assignment(html, "const EXTRA_IMAGES=")
    sources = data.get("sources", {})

    fields: dict[str, list[str]] = defaultdict(list)
    image_counts: Counter[str] = Counter()
    exact_keys: dict[tuple[object, ...], list[str]] = defaultdict(list)
    checked = 0

    for index, model in enumerate(data["m"]):
        if model[14] not in {"Global", "Europa"}:
            continue
        checked += 1
        label = display_name(model)
        is_film = len(model) > 17 and model[17] == "film"

        for field, position in (("diagonală", 3), ("lungime corp", 4), ("lățime corp", 5),
                                ("lungime ecran", 8), ("lățime ecran", 9)):
            if len(model) <= position or not isinstance(model[position], (int, float)) or model[position] <= 0:
                fields[field].append(label)

        if not is_film and (len(model) <= 6 or not model[6] or model[6] == "Necunoscută"):
            fields["formă cameră"].append(label)
        if len(model) <= 16 or not model[16]:
            fields["tip ecran"].append(label)

        named_source = f"{model[1]} — {model[18]}" if is_film and len(model) > 18 else str(model[1])
        row_source = model[17] if len(model) > 17 and isinstance(model[17], str) and model[17].startswith("http") else None
        if not row_source and not sources.get(named_source) and not sources.get(str(model[1])):
            fields["sursă explicită (metadate)"].append(label)

        status = image_status(index, model, bundles, extras)
        image_counts[status] += 1
        if status == "lipsă":
            fields["fotografie"].append(label)

        key = (model[0], model[1], model[3], model[14], model[17] if is_film else None,
               model[18] if is_film and len(model) > 18 else None)
        exact_keys[key].append(f"{label} [rândul {index}]")

    duplicates = [names[0] for names in exact_keys.values() if len(names) > 1]
    if duplicates:
        fields["posibil duplicat"].extend(duplicates)

    lines = [
        "## Raport lunar de completitudine",
        f"Verificate **{checked}** modele din piețele Global/Europa. Raportul semnalează lipsuri; nu modifică și nu publică date.",
        "",
        "| Verificare | Probleme |",
        "|---|---:|",
    ]
    for field in ("diagonală", "lungime corp", "lățime corp", "lungime ecran", "lățime ecran",
                  "formă cameră", "tip ecran", "sursă explicită (metadate)", "fotografie", "posibil duplicat"):
        lines.append(f"| {field} | {len(fields[field])} |")
    lines.extend(["", "### Exemple de verificat"])
    any_findings = False
    for field in ("lungime ecran", "lățime ecran", "tip ecran", "fotografie", "posibil duplicat"):
        names = list(dict.fromkeys(fields[field]))
        if not names:
            continue
        any_findings = True
        shown = ", ".join(names[:6])
        more = f" și încă {len(names) - 6}" if len(names) > 6 else ""
        lines.append(f"- **{field}:** {shown}{more}")
    if not any_findings:
        lines.append("- Nu au fost găsite lipsuri.")
    lines.extend(["", "### Starea fotografiilor", ""])
    for status in ("încorporată", "locală", "externă", "lipsă"):
        lines.append(f"- {status.capitalize()}: {image_counts[status]}")
    report = "\n".join(lines) + "\n"

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as stream:
            stream.write(report)
    print(report, end="")


if __name__ == "__main__":
    main()
