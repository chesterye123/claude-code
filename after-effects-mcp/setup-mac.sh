#!/usr/bin/env bash
# One-shot macOS setup: build the server, install the After Effects panel,
# and register the server with Claude Code and/or Claude Desktop.
set -euo pipefail

cd "$(dirname "$0")"
DIR="$(pwd)"
NAME="AfterEffectsMCP"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This script is for macOS." >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is not installed. Install the LTS version from https://nodejs.org and re-run." >&2
  exit 1
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if (( NODE_MAJOR < 18 )); then
  echo "Node.js 18 or newer is required (found $(node --version))." >&2
  exit 1
fi
# Absolute path: GUI apps like Claude Desktop don't inherit your shell PATH.
NODE_BIN="$(command -v node)"
SERVER="$DIR/build/index.js"

echo "==> Installing dependencies and building"
rm -rf node_modules build
npm ci --no-audit --no-fund

echo "==> Installing the bridge panel into After Effects (may ask for your Mac password)"
BRIDGE_OK=1
if ! npm run install-bridge; then
  BRIDGE_OK=0
  echo "!!  Panel not installed automatically. Copy this file by hand:" >&2
  echo "      $DIR/build/scripts/mcp-bridge-auto.jsx" >&2
  echo "    into: /Applications/Adobe After Effects <version>/Scripts/ScriptUI Panels/" >&2
fi

REGISTERED=0

if command -v claude >/dev/null 2>&1; then
  echo "==> Registering with Claude Code (user scope)"
  claude mcp remove -s user "$NAME" >/dev/null 2>&1 || true
  claude mcp add -s user "$NAME" -- "$NODE_BIN" "$SERVER"
  REGISTERED=1
fi

DESKTOP_DIR="$HOME/Library/Application Support/Claude"
if [[ -d "$DESKTOP_DIR" ]]; then
  echo "==> Registering with Claude Desktop"
  CONFIG="$DESKTOP_DIR/claude_desktop_config.json"
  if [[ -f "$CONFIG" ]]; then
    BACKUP="$CONFIG.bak.$(date +%Y%m%d%H%M%S)"
    cp "$CONFIG" "$BACKUP"
    echo "    Backed up existing config to: $BACKUP"
  fi
  CONFIG="$CONFIG" NAME="$NAME" NODE_BIN="$NODE_BIN" SERVER="$SERVER" node -e '
    const fs = require("fs");
    const { CONFIG, NAME, NODE_BIN, SERVER } = process.env;
    const raw = fs.existsSync(CONFIG) ? fs.readFileSync(CONFIG, "utf8").trim() : "";
    const cfg = raw ? JSON.parse(raw) : {};
    cfg.mcpServers = { ...cfg.mcpServers, [NAME]: { command: NODE_BIN, args: [SERVER] } };
    fs.writeFileSync(CONFIG, JSON.stringify(cfg, null, 2) + "\n");
  '
  echo "    Quit and reopen Claude Desktop to load it."
  REGISTERED=1
fi

if (( REGISTERED == 0 )); then
  echo "==> No Claude Code CLI or Claude Desktop found. Add this to your MCP client config:"
  cat <<EOF
{
  "mcpServers": {
    "$NAME": { "command": "$NODE_BIN", "args": ["$SERVER"] }
  }
}
EOF
fi

cat <<EOF

Done. Last steps, in After Effects:
  1. After Effects > Settings > Scripting & Expressions >
     tick "Allow Scripts to Write Files and Access Network"
  2. Restart After Effects
  3. Window > mcp-bridge-auto.jsx  (keep this panel open with "Auto-run commands" ticked)
EOF
if (( BRIDGE_OK == 0 )); then
  echo "  (Do the manual panel copy above first, or step 3 won't show the panel.)"
fi
