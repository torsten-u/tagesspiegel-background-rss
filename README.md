# Tagesspiegel Background Energie & Klima → RSS

Persönlicher RSS-Feed für die Übersichtsseite von  
**Tagesspiegel Background – Energie & Klima**.

## Warum?

Tagesspiegel bietet für diese Seite keinen RSS-Feed an.

Direkte automatisierte Abrufe der Seite werden mit HTTP 403 blockiert. Das betrifft unter anderem klassische HTTP-Clients und GitHub Actions.

Deshalb wird die bereits regulär in Safari geladene Seite lokal ausgelesen.

## Funktionsweise

Safari  
↓  
`generate_from_safari.py`  
↓  
`docs/feed.xml`  
↓  
GitHub Pages  
↓  
NetNewsWire

Das Skript liest Titel, Links und Teaser aus der in Safari geöffneten Übersichtsseite und erzeugt daraus einen RSS-Feed.

Geschützte Artikelinhalte werden nicht ausgelesen oder in den Feed übernommen.

## Aktualisierung

1. `https://background.tagesspiegel.de/energie-und-klima` in Safari öffnen.
2. `Tagesspiegel RSS aktualisieren.command` starten.
3. Dadurch wird `docs/feed.xml` neu erzeugt.
4. Änderung zu GitHub committen und pushen.

## RSS-Feed

`https://torsten-u.github.io/tagesspiegel-background-rss/feed.xml`

Der Feed kann direkt in NetNewsWire oder einem anderen RSS-Reader abonniert werden.
