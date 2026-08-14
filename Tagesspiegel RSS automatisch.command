#!/bin/bash
set -e

REPO="$HOME/GitHub/torsten"
URL="https://background.tagesspiegel.de/energie-und-klima"

cd "$REPO" || exit 1

echo "Tagesspiegel Background → RSS → GitHub"

echo "1/4 Safari lädt Tagesspiegel Background …"
echo "   Warte 30 Sekunden nach dem Start …"
sleep 30

OK=0

for A in 1 2 3 4 5; do
    echo "   Safari-Versuch $A/5 …"

    if osascript <<APPLESCRIPT
with timeout of 20 seconds
tell application "Safari"
    activate

    if (count of windows) = 0 then
        make new document with properties {URL:"$URL"}
    else
        set foundTab to missing value

        repeat with w in windows
            repeat with t in tabs of w
                try
                    if URL of t starts with "$URL" then
                        set foundTab to t
                        set current tab of w to t
                        set index of w to 1
                        exit repeat
                    end if
                end try
            end repeat

            if foundTab is not missing value then exit repeat
        end repeat

        if foundTab is missing value then
            tell front window to set current tab to (make new tab with properties {URL:"$URL"})
        else
            set URL of foundTab to "$URL"
        end if
    end if
end tell
end timeout
APPLESCRIPT
    then
        OK=1
        break
    fi

    if [ "$A" -lt 5 ]; then
        echo "   Noch nicht bereit; warte 15 Sekunden …"
        sleep 15
    fi
done

[ "$OK" -eq 1 ] || {
    echo "FEHLER: Safari nicht ansprechbar." >&2
    exit 1
}

PAGE=0

for i in {1..30}; do
    COUNT=$(osascript \
        -e 'with timeout of 10 seconds' \
        -e 'tell application "Safari" to do JavaScript "document.readyState + \":\" + document.querySelectorAll(\"a[href*=\\\"/energie-und-klima/\\\"]\").length" in current tab of front window' \
        -e 'end timeout' 2>/dev/null || true)

    if [[ "$COUNT" == complete:* ]]; then
        N="${COUNT#complete:}"

        if [[ "$N" =~ ^[0-9]+$ ]] && [ "$N" -gt 5 ]; then
            echo "   Seite geladen ($N passende Links)."
            PAGE=1
            break
        fi
    fi

    sleep 2
done

[ "$PAGE" -eq 1 ] || {
    echo "FEHLER: Seite nicht rechtzeitig geladen." >&2
    exit 1
}

echo "2/4 RSS erzeugen …"
python3 generate_from_safari.py

echo "3/4 Änderungen prüfen …"
git add docs/tagesspiegel.xml

if git diff --cached --quiet; then
    echo "   Keine inhaltliche Änderung am Feed."
    echo "FERTIG."
    exit 0
fi

git commit -m "Tagesspiegel RSS aktualisiert $(date '+%Y-%m-%d %H:%M')"

echo "4/4 Zu GitHub übertragen …"
git push origin main

echo "FERTIG: Feed aktualisiert und zu GitHub übertragen."