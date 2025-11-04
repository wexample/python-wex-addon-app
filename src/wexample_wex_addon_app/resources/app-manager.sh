#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AM_DIR="$APP_ROOT/.wex/python/app_manager"
REQUEST_ID="$(date '+%Y%m%d-%H%M%S-%N')-$$"

if [ "${1:-}" = "setup" ]; then
  # Create directory if missing
  mkdir -p "$AM_DIR"

  cd "$AM_DIR"

  # Ensure pdm is available
  if ! command -v pdm &>/dev/null; then
    echo "❌ Error: 'pdm' not found. Please install it first." >&2
    exit 1
  fi

  # Force PDM to use/create .venv in app_manager directory, ignoring any active venv
  export PDM_IGNORE_ACTIVE_VENV=1

  pdm install
  
  # Ensure pip is available in the venv
  "$AM_DIR/.venv/bin/python" -m ensurepip --upgrade 2>/dev/null || true
else
  exec "$AM_DIR/.venv/bin/python" "$AM_DIR/__main__.py" "${REQUEST_ID}" "${@}"
fi
