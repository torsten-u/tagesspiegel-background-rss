#!/usr/bin/env python3
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parent
OUT = REPO / "docs" / "tagesspiegel.xml"

JS = """
(() => {
  const out = [];
  const seen = new Set();

  for (const h of document.querySelectorAll("h2,h3")) {
    const title = (h.innerText || "").trim();
    if (!title || title.length < 8) continue;

    let node = h, link = null, container = null;

    for (let i = 0; i < 7 && node; i++, node = node.parentElement) {
      const links = Array.from(node.querySelectorAll?.("a[href]") || []);
      const a = links.find(a => {
        try {
          const u = new URL(a.href, location.href);
          return u.hostname === "background.tagesspiegel.de"
            && u.pathname.startsWith("/energie-und-klima/")
            && u.pathname.split("/").filter(Boolean).length >= 3
            && !u.pathname.includes("/themen/")
            && !u.pathname.includes("/autoren/")
            && !u.pathname.includes("/suche");
        } catch(e) { return false; }
      });
      if (a) { link = a.href; container = node; break; }
    }

    if (!link || seen.has(link)) continue;
    seen.add(link);

    const fullText = (container?.innerText || "").trim();
    let teaser = fullText.replace(title, "").trim()
      .replace(/\\n{3,}/g, "\\n\\n")
      .split("\\n").map(x => x.trim()).filter(Boolean)
      .filter(x => x !== title).slice(0, 8).join(" ");

    out.push({title, link, teaser});
  }
  return JSON.stringify(out);
})()
"""

def safari_js(js):
    p = subprocess.run([
        "osascript",
        "-e", 'tell application "Safari"',
        "-e", f'do JavaScript {json.dumps(js)} in current tab of front window',
        "-e", "end tell"
    ], capture_output=True, text=True)

    if p.returncode != 0:
        raise RuntimeError(
            p.stderr.strip() or "Safari/AppleScript-Fehler"
        )

    return p.stdout.strip()


items = json.loads(safari_js(JS))

items = [
    x for x in items
    if x["title"] not in {
        "Analysen und Nachrichten",
        "Letzte Briefing-Ausgabe"
    }
]

if not items:
    raise SystemExit(
        "Keine Artikel gefunden. Ist die Background-Seite der aktive Safari-Tab?"
    )

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

rss = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0">',
    '<channel>',
    '<title>Tagesspiegel Background – Energie &amp; Klima</title>',
    '<link>https://background.tagesspiegel.de/energie-und-klima</link>',
    '<description>RSS aus der in Safari geladenen Übersichtsseite von Tagesspiegel Background Energie &amp; Klima.</description>',
    '<language>de</language>',
    f'<lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>'
]

for it in items[:40]:
    title = escape(it["title"])
    link = escape(it["link"])
    teaser = escape(it.get("teaser") or "")

    rss += [
        "<item>",
        f"<title>{title}</title>",
        f"<link>{link}</link>",
        f'<guid isPermaLink="true">{link}</guid>'
    ]

    if teaser:
        rss.append(
            f"<description>{teaser}</description>"
        )

    rss.append(
        "</item>"
    )

rss += [
    "</channel>",
    "</rss>"
]

OUT.write_text(
    "\n".join(rss),
    encoding="utf-8"
)

print(
    f"{len(items)} Einträge gefunden."
)

print(
    f"RSS geschrieben: {OUT}"
)