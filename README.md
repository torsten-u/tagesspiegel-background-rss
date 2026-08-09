# Tagesspiegel Background Energie & Klima → RSS

Dieses kleine Repository erzeugt automatisch einen RSS-Feed aus der öffentlich
sichtbaren Übersichtsseite:

https://background.tagesspiegel.de/energie-und-klima

Es werden nur Metadaten übernommen: Titel, Teaser, Datum, Autor und Link.
Geschützte Artikeltexte werden nicht in den Feed kopiert.

## Einrichtung auf GitHub

### 1. Neues Repository anlegen

Auf GitHub oben rechts `+` → `New repository`.

Empfohlener Name:

`tagesspiegel-background-rss`

Das Repository kann **Public** sein; es enthält keine privaten Zugangsdaten.
`Add a README file` zunächst **nicht** auswählen.

### 2. Dateien hochladen

Den Inhalt dieses Pakets ins Repository übernehmen. Die Struktur muss so aussehen:

    .github/
      workflows/
        update-feed.yml
    docs/
      .gitkeep
    feedgen.py
    requirements.txt
    README.md

Wichtig: `.github` beginnt mit einem Punkt.

### 3. Workflow einmal manuell starten

Im Repository:

`Actions` → `Tagesspiegel RSS aktualisieren` → `Run workflow` → `Run workflow`

Nach erfolgreichem Lauf sollte die Datei `docs/feed.xml` im Repository erscheinen.

Falls GitHub nach einer Erlaubnis für Actions fragt, diese für das Repository aktivieren.

### 4. GitHub Pages einschalten

Im Repository:

`Settings` → `Pages`

Unter **Build and deployment**:

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/docs`
- `Save`

GitHub veröffentlicht anschließend den Ordner `docs`.

Die Feed-Adresse lautet dann normalerweise:

    https://DEIN-GITHUB-NAME.github.io/tagesspiegel-background-rss/feed.xml

`DEIN-GITHUB-NAME` durch den eigenen GitHub-Benutzernamen ersetzen.

### 5. In NetNewsWire abonnieren

In NetNewsWire:

`File` → `New Web Feed`

Die eben erzeugte GitHub-Pages-Adresse einfügen.

## Automatik

Der Workflow läuft zweimal täglich. Zusätzlich kann er unter `Actions`
jederzeit manuell gestartet werden.

## Wenn Tagesspiegel seine Seite ändert

Dann kann der Parser irgendwann keine Artikel mehr erkennen. Der Workflow
bricht in diesem Fall bewusst mit einer Fehlermeldung ab, statt einen leeren
Feed zu veröffentlichen.
