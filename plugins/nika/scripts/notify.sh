#!/usr/bin/env bash
# ──────────────────────────────────────────────────
# Nika OS — Desktop Notifications
#
# Cross-platform notification helper.
# Supports: macOS (osascript), Linux (notify-send),
# and falls back to terminal bell.
#
# Usage:
#   bash notify.sh "Title" "Message"
# ──────────────────────────────────────────────────

TITLE="${1:-Nika OS}"
MESSAGE="${2:-Notification}"

# ── macOS ──────────────────────────────────────────
if command -v osascript &>/dev/null; then
    osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\"" 2>/dev/null
    exit 0
fi

# ── Linux (notify-send) ───────────────────────────
if command -v notify-send &>/dev/null; then
    notify-send "$TITLE" "$MESSAGE" 2>/dev/null
    exit 0
fi

# ── Windows (powershell) ──────────────────────────
if command -v powershell.exe &>/dev/null; then
    powershell.exe -Command "
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        \$template = @\"
<toast>
  <visual>
    <binding template='ToastGeneric'>
      <text>$TITLE</text>
      <text>$MESSAGE</text>
    </binding>
  </visual>
</toast>
\"@
    " 2>/dev/null
    exit 0
fi

# ── Fallback: terminal bell ───────────────────────
printf '\a'
echo "[$TITLE] $MESSAGE"
