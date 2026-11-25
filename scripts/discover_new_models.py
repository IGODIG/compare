#!/usr/bin/env python3
"""Find newly listed GSMArena phones and add them to a review queue."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
CANDIDATES_PATH = ROOT / "data" / "new-model-candidates.json"
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

SOURCE_URL = "https://www.gsmarena.com/recent.php3"
SITE_URL = "https://www.gsmarena.com/"
PHONE_PATH = re.compile(r"^/?[a-z0-9_-]+-(\d+)\.php$", re.IGNORECASE)
SUPPORTED = {
    "samsung": "Samsung",
    "xiaomi": "Xiaomi",
    "redmi": "Xiaomi",
    "poco": "Xiaomi",
    "apple": "Apple",
    "oppo": "Oppo",
    "realme": "Realme",
    "honor": "Honor",
    "huawei": "Huawei",
    "oneplus": "OnePlus",
}
BRAND_WORDS = set(SUPPORTED) | {"galaxy", "iphone"}
NON_PHONE_WORDS = {"watch", "watches", "tab", "tablet", "tablets", "pad", "pads", "buds", "band"}


class PhoneLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: dict[str, object] | None = None
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href") and PHONE_PATH.match(str(attributes["href"])):
            self.current = {"href": str(attributes["href"]), "text": [], "image": ""}
        elif tag == "img" and self.current is not None:
            image = attributes.get("src") or attributes.get("data-src") or ""
            if image:
                self.current["image"] = str(image)

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current["text"].append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self.current is None:
            return
        parts = self.current["text"]
        name = " ".join(str(x) for x in parts if x).strip()
        if name:
            self.links.append(
                {
                    "name": re.sub(r"\s+", " ", name),
                    "url": urljoin(SITE_URL, str(self.current["href"])),
                    "image": urljoin(SITE_URL, str(self.current["image"])) if self.current["image"] else "",
                }
            )
        self.current = None


def canonical_brand(name: str) -> str | None:
    first = re.sub(r"[^a-z0-9]", "", name.casefold().split()[0]) if name.split() else ""
    return SUPPORTED.get(first)


def model_key(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.casefold())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    tokens = re.findall(r"[a-z0-9]+", normalized)
    return "".join(token for token in tokens if token not in BRAND_WORDS)


def load_known(data: dict[str, object]) -> tuple[set[tuple[str, str]], set[str]]:
    keys: set[tuple[str, str]] = set()
    ids: set[str] = set()
    for model in data.get("m", []):
        brand = str(model[0])
        brand_key = "Xiaomi" if brand in {"Redmi", "Poco"} else brand
        for alias in str(model[1]).split(" / "):
            key = model_key(alias)
            if key:
                keys.add((brand_key, key))
    for url in data.get("sources", {}).values():
        match = re.search(r"-(\d+)\.php(?:$|\?)", str(url))
        if match:
            ids.add(match.group(1))
    return keys, ids


def fetch_latest() -> str:
    request = Request(
        SOURCE_URL,
        headers={"User-Agent": "Magnet-Phone-Compatibility-Model-Discovery/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise SystemExit(f"Nu am putut citi catalogul GSMArena: {exc}") from exc


def discover() -> list[dict[str, str]]:
    parser = PhoneLinkParser()
    parser.feed(fetch_latest())
    if not parser.links:
        raise SystemExit("GSMArena nu a returnat modele. Verifică structura paginii recent.php3.")

    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    known_keys, known_ids = load_known(data)
    found: dict[str, dict[str, str]] = {}
    for item in parser.links:
        path = urlparse(item["url"]).path
        match = PHONE_PATH.match(path)
        if not match:
            continue
        device_id = match.group(1)
        words = set(re.findall(r"[a-z0-9]+", item["name"].casefold()))
        if words & NON_PHONE_WORDS:
            continue
        brand = canonical_brand(item["name"])
        if not brand or device_id in known_ids:
            continue
        key = model_key(item["name"])
        if not key or (brand, key) in known_keys:
            continue
        found[device_id] = {
            "id": device_id,
            "brand": brand,
            "name": item["name"],
            "source_url": item["url"],
            "image_url": item["image"],
            "status": "needs_market_specs_and_image_review",
        }
    return list(found.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Find newly listed GSMArena phone models.")
    parser.add_argument("--dry-run", action="store_true", help="Print new candidates without changing the queue file.")
    args = parser.parse_args()
    additions = discover()
    current = {"schema_version": 1, "candidates": []}
    if CANDIDATES_PATH.exists():
        current = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))
    existing = {str(row["id"]) for row in current.get("candidates", [])}
    new_rows = [row for row in additions if row["id"] not in existing]
    if not new_rows:
        print("Nu au fost găsite modele noi pentru coada de verificare.")
        return

    if args.dry_run:
        print(json.dumps(new_rows, ensure_ascii=False, indent=2))
        return

    today = datetime.now(timezone.utc).date().isoformat()
    for row in new_rows:
        row["discovered_on"] = today
    current["last_scan_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    current.setdefault("schema_version", 1)
    current.setdefault("candidates", []).extend(new_rows)
    CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES_PATH.write_text(
        json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Am adăugat {len(new_rows)} modele-candidat în {CANDIDATES_PATH.relative_to(ROOT)}.")


if __name__ == "__main__":
    try:
        main()
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Date invalide pentru descoperirea modelelor: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
