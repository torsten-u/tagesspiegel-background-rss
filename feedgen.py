#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from feedgen.feed import FeedGenerator

START_URL = "https://background.tagesspiegel.de/energie-und-klima"
BASE_HOST = "background.tagesspiegel.de"
OUTPUT = Path("docs/feed.xml")
MAX_ITEMS = 40

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Navigations-/Übersichtsseiten, die keine einzelnen Meldungen sind.
EXCLUDED_SLUGS = {
    "briefing", "monitoring", "suche", "analysen", "nachrichten",
    "analysen-und-hintergruende", "standpunkte", "portraets",
    "förderung", "foerderung", "briefing-ausgaben",
    "gesetzgebungsverfahren", "ausblick", "rueckblick", "rückblick",
}

DATE_RE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")


def fetch_requests(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    if len(r.text) < 5000:
        raise RuntimeError(f"Verdächtig kurze Antwort ({len(r.text)} Zeichen)")
    return r.text


def fetch_browser(url: str) -> str:
    # Fallback, falls Tagesspiegel normale Server-Abrufe blockiert.
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=HEADERS["User-Agent"],
            locale="de-DE",
            viewport={"width": 1440, "height": 1000},
        )
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        content = page.content()
        browser.close()
        return content


def fetch(url: str) -> str:
    try:
        return fetch_requests(url)
    except Exception as e:
        print(f"Normaler Abruf fehlgeschlagen: {e}", file=sys.stderr)
        print("Versuche Chromium-Fallback …", file=sys.stderr)
        return fetch_browser(url)


def is_article_url(url: str) -> bool:
    p = urlparse(url)
    if p.netloc and p.netloc != BASE_HOST:
        return False
    path = p.path.rstrip("/")
    if not path.startswith("/energie-und-klima/"):
        return False

    parts = [x for x in path.split("/") if x]
    # Mindestens: energie-und-klima / bereich / artikel-slug
    if len(parts) < 3:
        return False

    last = parts[-1].lower()
    if last in EXCLUDED_SLUGS:
        return False

    # Typische Taxonomie-/Suchlinks aussortieren
    if "/themen/" in path or "/autoren/" in path or "/suche" in path:
        return False

    return True


def find_link_for_heading(heading) -> str | None:
    # 1) Link im Heading
    a = heading.find("a", href=True)
    if a and is_article_url(urljoin(START_URL, a["href"])):
        return urljoin(START_URL, a["href"])

    # 2) Heading selbst liegt in einem Link
    a = heading.find_parent("a", href=True)
    if a and is_article_url(urljoin(START_URL, a["href"])):
        return urljoin(START_URL, a["href"])

    # 3) In Kartenstrukturen einige Ebenen nach oben suchen
    parent = heading
    for _ in range(6):
        parent = parent.parent
        if not parent:
            break
        candidates = parent.find_all("a", href=True, limit=12)
        for cand in candidates:
            u = urljoin(START_URL, cand["href"])
            if is_article_url(u):
                return u
    return None


def homepage_candidates(doc: str) -> list[dict]:
    soup = BeautifulSoup(doc, "html.parser")
    items = []
    seen = set()

    # Die eigentlichen Inhalte erscheinen auf der Startseite als H3-Karten.
    for h in soup.find_all(["h3", "h2"]):
        title = " ".join(h.stripped_strings).strip()
        if not title or len(title) < 8:
            continue

        url = find_link_for_heading(h)
        if not url or url in seen:
            continue

        seen.add(url)
        items.append({"title": title, "url": url})

    # Fallback: falls sich das Markup ändert, Links mit längeren Linktexten einsammeln.
    if len(items) < 5:
        for a in soup.find_all("a", href=True):
            url = urljoin(START_URL, a["href"])
            title = " ".join(a.stripped_strings).strip()
            if (
                is_article_url(url)
                and url not in seen
                and len(title) >= 15
            ):
                seen.add(url)
                items.append({"title": title, "url": url})

    return items[:MAX_ITEMS]


def meta_content(soup: BeautifulSoup, *, prop=None, name=None) -> str | None:
    attrs = {}
    if prop:
        attrs["property"] = prop
    if name:
        attrs["name"] = name
    tag = soup.find("meta", attrs=attrs)
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def enrich(item: dict) -> dict:
    try:
        doc = fetch_requests(item["url"])
    except Exception:
        # Für Einzelartikel kein Browser-Fallback erzwingen; Startseiten-Metadaten reichen notfalls.
        return item

    soup = BeautifulSoup(doc, "html.parser")

    title = (
        meta_content(soup, prop="og:title")
        or meta_content(soup, name="twitter:title")
        or item["title"]
    )
    # Tagesspiegel hängt gelegentlich Branding an den OG-Titel.
    title = re.sub(r"\s*-\s*Tagesspiegel Background\s*$", "", title).strip()

    description = (
        meta_content(soup, prop="og:description")
        or meta_content(soup, name="description")
        or meta_content(soup, name="twitter:description")
        or ""
    )

    published = (
        meta_content(soup, prop="article:published_time")
        or meta_content(soup, name="date")
        or ""
    )

    if not published:
        text = soup.get_text(" ", strip=True)
        m = re.search(r"veröffentlicht am\s+" + DATE_RE.pattern, text, re.I)
        if m:
            published = m.group(1)

    author = meta_content(soup, name="author") or ""

    item.update(
        title=title,
        description=description,
        published=published,
        author=author,
    )
    return item


def parse_date(value: str):
    if not value:
        return None
    try:
        dt = dateparser.parse(value, dayfirst=True)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def build_feed(items: list[dict]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fg = FeedGenerator()
    fg.id(START_URL)
    fg.title("Tagesspiegel Background – Energie & Klima")
    fg.link(href=START_URL, rel="alternate")
    fg.link(href="feed.xml", rel="self")
    fg.description(
        "Automatisch erzeugter RSS-Feed aus der öffentlich sichtbaren "
        "Übersichtsseite von Tagesspiegel Background Energie & Klima."
    )
    fg.language("de")
    fg.lastBuildDate(datetime.now(timezone.utc))

    # Neueste Datumswerte möglichst nach vorn; undatierte behalten Homepage-Reihenfolge.
    dated = []
    for idx, it in enumerate(items):
        dated.append((parse_date(it.get("published", "")), idx, it))
    dated.sort(key=lambda x: (x[0] is not None, x[0] or datetime.min.replace(tzinfo=timezone.utc), -x[1]), reverse=True)

    for dt, _, item in dated:
        fe = fg.add_entry(order="append")
        fe.id(item["url"])
        fe.title(item["title"])
        fe.link(href=item["url"])

        desc = item.get("description", "")
        if desc:
            fe.description(html.escape(desc))

        if item.get("author"):
            fe.author({"name": item["author"]})

        if dt:
            fe.pubDate(dt)

    fg.rss_file(str(OUTPUT), pretty=True)


def main():
    doc = fetch(START_URL)
    candidates = homepage_candidates(doc)
    if not candidates:
        raise SystemExit("Keine Artikel gefunden – Seitenstruktur möglicherweise geändert.")

    print(f"{len(candidates)} Artikelkandidaten gefunden.")
    enriched = []
    for i, item in enumerate(candidates, 1):
        print(f"[{i:02d}/{len(candidates):02d}] {item['title'][:80]}")
        enriched.append(enrich(item))

    build_feed(enriched)
    print(f"Feed geschrieben: {OUTPUT}")


if __name__ == "__main__":
    main()
