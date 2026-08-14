#!/bin/bash
set -e

REPO="$HOME/GitHub/torsten"
PLIST="$HOME/Library/LaunchAgents/de.torsten.tagesspiegel-rss.plist"
LOGDIR="$HOME/Library/Logs/tagesspiegel-rss"

mkdir -p "$LOGDIR"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>de.torsten.tagesspiegel-rss</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$REPO/Tagesspiegel RSS automatisch.command</string>
    </array>

    <key>StartCalendarInterval</key>
    <array>
        <dict>
            <key>Hour</key>
            <integer>7</integer>
            <key>Minute</key>
            <integer>17</integer>
        </dict>
        <dict>
            <key>Hour</key>
            <integer>15</integer>
            <key>Minute</key>
            <integer>17</integer>
        </dict>
    </array>

    <key>StandardOutPath</key>
    <string>$LOGDIR/output.log</string>

    <key>StandardErrorPath</key>
    <string>$LOGDIR/error.log</string>
</dict>
</plist>
EOF

launchctl bootout gui/$(id -u) "$PLIST" 2>/dev/null || true
launchctl bootstrap gui/$(id -u) "$PLIST"

echo "Automation installiert."
echo "Läuft täglich um 07:17 und 15:17 Uhr."
echo "Logs: $LOGDIR"