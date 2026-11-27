#!/usr/bin/env python3
"""Discover Moldova-market phone models from local retailer catalogs.

Retail listings are availability signals only. A candidate still needs exact
market, dimensions, display/camera traits, and image verification before use.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from discover_official_models import (
    CANDIDATES_PATH,
    DATA_PATH,
    PATTERNS,
    ProductLinkParser,
    clean,
    extract_models,
    fetch,
    model_key_for_brand,
)

ROOT = Path(__file__).resolve().parents[1]
RETAILERS = {
    "Orange Moldova": "https://www.orange.md/ro/shop/catalog/telefoane/toate-telefoanele",
    "Moldcell": "https://eshop.moldcell.md/ro/catalog/telefoane",
    "Darwin": "https://darwin.md/telefoane/smartphone",
}


def stable_slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def brand_matches(title: str) -> list[tuple[str, str]]:
    found = []
    for brand in PATTERNS:
        for model in extract_models(title, brand):
            found.append((brand, model))
    return found


def scan() -> tuple[list[dict], list[str]]:
    known: set[tuple[str, str]] = set()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for model in data.get("m", []):
        for alias in str(model[1]).split(" / "):
            known.add(model_key_for_brand(alias, str(model[0])))

    current = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8")) if CANDIDATES_PATH.exists() else {"candidates": []}
    rows = current.get("candidates", [])
    pending = {
        model_key_for_brand(str(row.get("name", "")), str(row.get("brand", ""))): row
        for row in rows
    }
    found: dict[tuple[str, str], dict] = {}
    successes: list[str] = []
    for retailer, url in RETAILERS.items():
        try:
            text = fetch(url)
            parser = ProductLinkParser()
            parser.feed(text)
            links = parser.links
            successes.append(retailer)
        except Exception as exc:
            print(f"Sursă indisponibilă — {retailer}: {exc}", file=sys.stderr)
            continue

        for title, link in links:
            title = clean(title)
            if not title:
                continue
            for brand, name in brand_matches(title):
                key = model_key_for_brand(name, brand)
                if not key[1] or key in known:
                    continue
                row = found.setdefault(key, {
                    "id": "moldova-retail-" + stable_slug(brand + "-" + key[1]),
                    "brand": brand,
                    "name": name,
                    "market": "Moldova",
                    "status": "needs_market_specs_and_image_review",
                    "retail_sources": [],
                })
                source = {"name": retailer, "url": link}
                if source not in row["retail_sources"]:
                    row["retail_sources"].append(source)
                if key in pending:
                    existing_sources = pending[key].setdefault("retail_sources", [])
                    if source not in existing_sources:
                        existing_sources.append(source)

    # Keep scan results out of the live catalog. They only enter the review queue.
    return list(found.values()), successes


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Scan Moldova phone retailers for model candidates.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    found, successes = scan()
    if not successes:
        raise SystemExit("Niciun catalog local nu a putut fi citit; coada nu a fost modificată.")
    print("Cataloage citite: " + ", ".join(successes))
    if args.dry_run:
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return

    current = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8")) if CANDIDATES_PATH.exists() else {"schema_version": 1, "candidates": []}
    rows = current.setdefault("candidates", [])
    by_key = {
        model_key_for_brand(str(row.get("name", "")), str(row.get("brand", ""))): row
        for row in rows
    }
    # A model already queued by the brand scan gets the local retailer evidence too.
    for candidate in found:
        key = model_key_for_brand(candidate["name"], candidate["brand"])
        if key in by_key:
            row = by_key[key]
            target = row.setdefault("retail_sources", [])
            for source in candidate["retail_sources"]:
                if source not in target:
                    target.append(source)
        else:
            rows.append(candidate)
            by_key[key] = candidate
    current["last_moldova_retail_scan_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    current.setdefault("schema_version", 1)
    CANDIDATES_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Am adăugat {len(found)} modele-candidat local verificate ca listare în Moldova.")


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    main()
