#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AM_DIR="$APP_ROOT/.wex/python/app_manager"
REQUEST_ID="$(date '+%Y%m%d-%H%M%S-%N')-$$"

CONFIG_FILE="/etc/wex.conf"

if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
fi

if [[ -z "${CORE_BIN:-}" ]]; then
    CORE_BIN="$(which wex 2>/dev/null || true)"
fi

if [[ -z "${CORE_BIN:-}" ]]; then
    echo "Error: Unable to locate 'wex'."
    echo "No CORE_BIN found in $CONFIG_FILE and 'which wex' returned nothing."
    exit 1
fi

CORE_DIR="$(dirname "$CORE_BIN")"
WEX_ROOT="$(dirname "$CORE_DIR")"
VENV_PATH="$WEX_ROOT/.venv"
PYTHON_BIN="$VENV_PATH/bin/python"

# Ensure the shared venv exists
if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "❌ Error: Shared venv not found at: $VENV_PATH"
    echo "Expected python at: $PYTHON_BIN"
    exit 1
fi

if [[ "${1:-}" = "setup" ]]; then
    # Setup only prepares the app_manager folder; venv already exists elsewhere.
    mkdir -p "$AM_DIR"

    echo "📥 Installing dependencies for app_manager using shared venv..."
    "$PYTHON_BIN" -m pip install -r "$AM_DIR/requirements.txt" 2>/dev/null || true

    echo "✅ Setup complete (using shared venv)"

else
    # Normal execution using shared venv
    exec "$PYTHON_BIN" "$AM_DIR/__main__.py" "$REQUEST_ID" "$@"
fi
