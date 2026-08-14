#!/bin/bash
PLIST="$HOME/Library/LaunchAgents/de.torsten.tagesspiegel-rss.plist"
launchctl bootout gui/$(id -u) "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "Automation entfernt."
