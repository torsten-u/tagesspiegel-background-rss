#!/bin/bash
cd "$(dirname "$0")"
echo "Tagesspiegel Background → RSS"
echo
echo "Background-Seite bitte als aktiven Safari-Tab geöffnet lassen."
echo
python3 generate_from_safari.py
STATUS=$?
echo
if [ $STATUS -eq 0 ]; then
  echo "Fertig: docs/feed.xml wurde aktualisiert."
else
  echo "Fehler beim Aktualisieren."
fi
echo
read -n 1 -s -r -p "Taste drücken zum Schließen …"
