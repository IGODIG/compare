#!/usr/bin/env python3
"""Keep downloaded phone photos small enough for quick mobile loading."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_IMAGE_BYTES = 600 * 1024
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    manifest = json.loads((ROOT / "data" / "phone-images.json").read_text(encoding="utf-8"))
    images = manifest.get("images", {})
    paths = {
        (ROOT / record["file"]).resolve()
        for record in images.values()
        if isinstance(record.get("file"), str) and record["file"].startswith("assets/")
    }
    failures: list[str] = []
    total_bytes = 0
    for path in sorted(paths):
        if ROOT not in path.parents or not path.is_file():
            failures.append(f"Imagine locală lipsă sau în afara proiectului: {path}")
            continue
        size = path.stat().st_size
        total_bytes += size
        if size > MAX_IMAGE_BYTES:
            failures.append(
                f"{path.relative_to(ROOT)} are {size / 1024:.0f} KB; limita este "
                f"{MAX_IMAGE_BYTES / 1024:.0f} KB. Redimensionează și comprimă fotografia."
            )

    print(
        f"Fotografii locale: {len(paths)} · {total_bytes / 1024 / 1024:.2f} MB total · "
        f"limită {MAX_IMAGE_BYTES / 1024:.0f} KB/fișier."
    )
    if failures:
        print("Verificarea bugetului de imagini a găsit probleme:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("OK: toate fotografiile se încadrează în buget.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
