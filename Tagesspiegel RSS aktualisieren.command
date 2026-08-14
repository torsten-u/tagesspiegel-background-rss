#!/bin/bash
set -e

REPO="$HOME/GitHub/torsten"

cd "$REPO" || exit 1

echo "Tagesspiegel Background → RSS → GitHub"

echo "1/3 RSS aus aktuellem Safari-Tab erzeugen …"
python3 generate_from_safari.py

echo "2/3 Änderungen prüfen …"
git add docs/tagesspiegel.xml

if git diff --cached --quiet; then
    echo "Keine inhaltliche Änderung am Feed."
    exit 0
fi

git commit -m "Tagesspiegel RSS aktualisiert $(date '+%Y-%m-%d %H:%M')"

echo "3/3 Zu GitHub übertragen …"
git push origin main

echo "FERTIG."