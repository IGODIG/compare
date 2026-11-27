#!/usr/bin/env python3
"""Collect phone candidates from official brand feeds and product catalogs."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from discover_new_models import model_key

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
CANDIDATES_PATH = ROOT / "data" / "new-model-candidates.json"
USER_AGENT = "Magnet-Phone-Model-Discovery/1.0 (GitHub Actions; public official feeds)"
RECENT_DAYS = 45

FEEDS = {
    "Samsung Global Newsroom": ("Samsung", "https://news.samsung.com/global/feed"),
    "Apple Newsroom": ("Apple", "https://www.apple.com/newsroom/rss-feed.rss"),
    "Huawei Press Releases": ("Huawei", "https://www.huawei.com/en/rss-feeds/huawei-updates/rss"),
}
PAGES = {
    "Xiaomi Global phones": ("Xiaomi", "https://www.mi.com/global/mobile/"),
    "OPPO Global catalog": ("Oppo", "https://www.oppo.com/en/newsroom/"),
    "OnePlus Global press releases": ("OnePlus", "https://www.oneplus.com/global/press-releases"),
    "HONOR Global News": ("Honor", "https://www.hihonor.com/global/news/"),
}

PATTERNS = {
    "Samsung": re.compile(r"\bGalaxy\s+(?:S|Z|A|M|F|XCover)\s*\d{1,3}[A-Za-z]?(?:\s*\+(?:\s*5G)?|\s+(?:5G|FE|Ultra|Plus|Pro|Edge|Fold|Flip|Classic|Core|Lite)){0,4}(?![A-Za-z0-9])", re.I),
    "Apple": re.compile(r"\biPhone\s+(?:Air|SE|\d{1,2})(?:\s+(?:Pro|Max|Plus|mini|e)){0,3}\b", re.I),
    "Xiaomi": re.compile(r"\b(?:Xiaomi\s+\d{1,2}[A-Za-z]?(?:\s+(?:Pro|Max|Ultra|T|Lite|Civi)){0,3}|Redmi\s+(?:Note\s+)?[A-Z]?\d{1,3}[A-Za-z]?(?:\s+(?:Pro|Max|Plus|Ultra|5G|4G|Turbo)){0,4}|POCO\s+[A-Z]?\d{1,2}[A-Za-z]?(?:\s+(?:Pro|Max|Ultra|Plus|5G|4G)){0,3})\b", re.I),
    "Oppo": re.compile(r"\bOPPO\s+(?:Find\s+[NX]\s*\d{1,2}[A-Za-z]?(?:\s+(?:Pro|Max|Ultra|Plus)){0,3}|Reno\s*\d{1,2}[A-Za-z]?(?:\s+(?:Pro|Max|Ultra|Plus|F|FS|Lite|5G|4G)){0,4}|[AFK]\s*\d{1,3}[A-Za-z]?(?:\s+(?:Pro|Max|Plus|Ultra|Lite|5G|4G)){0,4})\b", re.I),
    "OnePlus": re.compile(r"\bOnePlus\s+(?:Nord\s+)?(?:N\s*)?\d{1,2}[A-Za-z]?(?:\s+(?:R|T|Pro|Max|Ultra|Plus|CE|Lite|5G|4G|Open)){0,4}\b", re.I),
    "Huawei": re.compile(r"\bHUAWEI\s+(?:Pura|Mate|nova|Pocket)\s*[A-Z]?\d{1,2}[A-Za-z]?(?:\s+(?:Pro|Max|Ultra|Plus|Fold|Flip|X)){0,4}\b", re.I),
    "Honor": re.compile(r"\bHONOR\s+(?:Magic|X|V|N)\s*\d{1,2}[A-Za-z]?(?:\s+(?:Pro|Max|Ultra|Plus|Lite|Fold|Flip|R|GT)){0,4}\b", re.I),
}


class ProductLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.active: tuple[str, list[str]] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            values = dict(attrs)
            href = values.get("href") or ""
            if href:
                title = values.get("title") or ""
                self.active = (str(href), [str(title)] if title else [])

    def handle_data(self, data: str) -> None:
        if self.active and data.strip():
            self.active[1].append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.active:
            href, parts = self.active
            self.links.append((" ".join(parts).strip(), href))
            self.active = None


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/html;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def clean(value: str) -> str:
    value = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", value, flags=re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def parse_feed(source: str, text: str) -> list[tuple[str, str, datetime | None]]:
    result: list[tuple[str, str, datetime | None]] = []
    for block in re.findall(r"<(?:item|entry)\b[^>]*>(.*?)</(?:item|entry)\s*>", text, flags=re.I | re.S):
        title = re.search(r"<title(?:\s[^>]*)?>(.*?)</title\s*>", block, flags=re.I | re.S)
        link = re.search(r"<link(?:\s[^>]*?href=[\"']([^\"']+)[\"'][^>]*)?\s*>(?:\s*([^<]+)\s*</link>)?", block, flags=re.I | re.S)
        date = re.search(r"<(?:pubDate|published|updated)\b[^>]*>(.*?)</(?:pubDate|published|updated)\s*>", block, flags=re.I | re.S)
        if not title or not link:
            continue
        target = link.group(1) or link.group(2) or ""
        published = None
        if date:
            try:
                published = parsedate_to_datetime(clean(date.group(1)))
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass
        result.append((clean(title.group(1)), urljoin(source, html.unescape(target.strip())), published))
    return result


def xiaomi_products(text: str) -> list[tuple[str, str, datetime | None]]:
    rows = []
    decoded = html.unescape(text)
    for encoded in re.findall(r'''data-ot-expose-custom=["']([^"']+)["']''', text, flags=re.I):
        try:
            event = json.loads(html.unescape(encoded))
        except json.JSONDecodeError:
            continue
        title = str(event.get("elementTitle", ""))
        link = str(event.get("link", ""))
        title = re.sub(r"^image_", "", title, flags=re.I).strip()
        if link and re.search(r"\b(?:Xiaomi\s+\d|Redmi\s+(?:Note\s+)?\w*\d|POCO\s+\w*\d)\b", title, flags=re.I):
            rows.append((title, urljoin("https://www.mi.com", link), None))
    # Some catalog cards expose product links directly instead of analytics metadata.
    for match in re.finditer(r"""href=["'](?P<url>(?:https?:)?//www\.mi\.com/global/product/[^"']+|/global/product/[^"']+)["']""", decoded, flags=re.I):
        url = urljoin("https://www.mi.com", html.unescape(match.group("url")))
        slug = urlparse(url).path.rstrip("/").split("/")[-1]
        name = re.sub(r"[-_]+", " ", slug).strip().title()
        name = re.sub(r"\bRedmi\b", "Redmi", name, flags=re.I)
        name = re.sub(r"\bPoco\b", "POCO", name, flags=re.I)
        if re.search(r"\b(?:Xiaomi\s+\d|Redmi\s+(?:Note\s+)?\w*\d|POCO\s+\w*\d)\b", name, flags=re.I):
            rows.append((name, url, None))
    return rows


def oppo_products(text: str) -> list[tuple[str, str, datetime | None]]:
    marker = re.search(r"[\"']navProduct[\"']\s*:", text)
    if not marker:
        return []
    try:
        groups, _ = json.JSONDecoder().raw_decode(text[marker.end() :].lstrip())
    except json.JSONDecodeError:
        return []
    rows = []
    for group in groups if isinstance(groups, list) else []:
        if "phone" not in str(group.get("title", "")).casefold():
            continue
        for product in group.get("products", []):
            name, link = str(product.get("title", "")).strip(), str(product.get("link", "")).strip()
            if name and link:
                rows.append((name, urljoin("https://www.oppo.com", link), None))
    return rows


def page_links(source: str, text: str) -> list[tuple[str, str, datetime | None]]:
    parser = ProductLinkParser()
    parser.feed(text)
    rows = []
    date_pattern = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b", re.I)
    for name, link in parser.links:
        if not name:
            continue
        published = None
        match = date_pattern.search(name)
        if match:
            for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"):
                try:
                    published = datetime.strptime(match.group(0), fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
        rows.append((name, urljoin(source, link), published))
    return rows


def extract_models(title: str, brand: str) -> list[str]:
    return list(dict.fromkeys(re.sub(r"\s+", " ", m.group(0)).strip(" ,:.-") for m in PATTERNS[brand].finditer(title)))


def model_key_for_brand(name: str, brand: str) -> tuple[str, str]:
    brand_alias = {"Redmi": "Xiaomi", "Poco": "Xiaomi"}.get(brand, brand)
    return brand_alias, model_key(name)


def make_id(brand: str, name: str) -> str:
    key = unicodedata.normalize("NFKD", model_key(name))
    key = "".join(c for c in key if not unicodedata.combining(c))
    return "official-" + re.sub(r"[^a-z0-9]+", "-", brand.casefold()).strip("-") + "-" + re.sub(r"[^a-z0-9]+", "-", key).strip("-")


def scan(group: str) -> tuple[list[dict[str, str]], list[str]]:
    priority = {"Samsung", "Apple", "Xiaomi"}
    source_map = FEEDS | PAGES
    successes: list[str] = []
    found: dict[str, dict[str, str]] = {}
    known: set[tuple[str, str]] = set()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for model in data.get("m", []):
        for alias in str(model[1]).split(" / "):
            known.add(model_key_for_brand(alias, str(model[0])))

    candidates_path = CANDIDATES_PATH
    existing = json.loads(candidates_path.read_text(encoding="utf-8")) if candidates_path.exists() else {"candidates": []}
    known.update(model_key_for_brand(str(row.get("name", "")), str(row.get("brand", ""))) for row in existing.get("candidates", []))

    for source_name, (brand, url) in source_map.items():
        if group == "priority" and brand not in priority:
            continue
        if group == "others" and brand in priority:
            continue
        try:
            text = fetch(url)
            if source_name == "Xiaomi Global phones":
                items = xiaomi_products(text)
            elif source_name == "OPPO Global catalog":
                items = oppo_products(text)
            elif source_name in FEEDS:
                items = parse_feed(url, text)
                if not items:
                    raise ValueError("feed fără articole XML/RSS")
            else:
                items = page_links(url, text)
                if source_name == "OnePlus Global press releases":
                    # Ignore navigation/footer links and historical releases without a date.
                    items = [item for item in items if item[2] is not None]
            successes.append(source_name)
        except Exception as exc:
            print(f"Sursă indisponibilă — {source_name}: {exc}", file=sys.stderr)
            continue

        cutoff = datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)
        for title, article_url, published in items:
            if published and published.astimezone(timezone.utc) < cutoff:
                continue
            names = extract_models(title, brand)
            for name in names:
                key = model_key_for_brand(name, brand)
                if not key[1] or key in known:
                    continue
                entry_id = make_id(brand, name)
                found.setdefault(entry_id, {
                    "id": entry_id,
                    "brand": brand,
                    "name": name,
                    "source": source_name,
                    "source_url": article_url,
                    "market": "global_source_check_exact_sales_region",
                    "status": "needs_market_specs_and_image_review",
                })
                known.add(key)
    return list(found.values()), successes


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan official brand sources for new phone candidates.")
    parser.add_argument("--group", choices=("priority", "others", "all"), default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    found, successes = scan(args.group)
    if not successes:
        raise SystemExit("Nicio sursă oficială nu a putut fi citită; coada nu a fost modificată.")
    print(f"Surse citite ({args.group}): " + ", ".join(successes))
    if not found:
        print("Nu au apărut modele-candidat noi.")
        return
    if args.dry_run:
        print(json.dumps(found, ensure_ascii=False, indent=2))
        return
    current = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8")) if CANDIDATES_PATH.exists() else {"schema_version": 1, "candidates": []}
    current["last_official_scan_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    current.setdefault("schema_version", 1)
    current.setdefault("candidates", []).extend(found)
    CANDIDATES_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Am adăugat {len(found)} modele-candidat pentru verificare.")


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    main()
