#!/usr/bin/env bash
# claude-statusline installer.
#   Install:   curl -fsSL https://raw.githubusercontent.com/ivantss/claude-statusline-mac/main/install.sh | bash
#   Uninstall: curl -fsSL https://raw.githubusercontent.com/ivantss/claude-statusline-mac/main/install.sh | bash -s -- --uninstall
set -euo pipefail

REPO_RAW="https://raw.githubusercontent.com/ivantss/claude-statusline-mac/main"
DIR="$HOME/.claude/claude-statusline"
SETTINGS="$HOME/.claude/settings.json"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "python3 is required (macOS: xcode-select --install ; Linux: your package manager)." >&2
  exit 1
fi

mkdir -p "$HOME/.claude"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

if [ "${1:-}" = "--uninstall" ]; then
  "$PY" - "$SETTINGS" "$DIR" <<'EOF'
import json, sys
path, d = sys.argv[1], sys.argv[2]
s = json.load(open(path))
backup = s.pop("_claude_statusline_previous", None)
if d in json.dumps(s.get("statusLine", "")):
    if backup: s["statusLine"] = backup
    else: s.pop("statusLine", None)
json.dump(s, open(path, "w"), indent=2)
EOF
  rm -rf "$DIR"
  echo "claude-statusline removed. Restart Claude Code."
  exit 0
fi

mkdir -p "$DIR"
# Local copy next to this script (git clone) wins; otherwise download.
SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)/statusline.py"
if [ -f "$SRC" ]; then
  cp "$SRC" "$DIR/statusline.py"
else
  curl -fsSL "$REPO_RAW/statusline.py" -o "$DIR/statusline.py"
fi
chmod +x "$DIR/statusline.py"

cp "$SETTINGS" "$SETTINGS.bak-statusline"
"$PY" - "$SETTINGS" "$PY" "$DIR/statusline.py" <<'EOF'
import json, sys
path, py, script = sys.argv[1:4]
s = json.load(open(path))
old = s.get("statusLine")
if old and script not in json.dumps(old):
    s["_claude_statusline_previous"] = old
s["statusLine"] = {"type": "command", "command": f"{py} {script}", "refreshInterval": 30}
json.dump(s, open(path, "w"), indent=2)
EOF

echo "claude-statusline installed → $DIR"
echo "Backup of your settings: $SETTINGS.bak-statusline"
echo "Restart Claude Code to see it."
