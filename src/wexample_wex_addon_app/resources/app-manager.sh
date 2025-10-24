#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AM_DIR="$APP_ROOT/.wex/python/app_manager"
WEX_TASK_ID="$(date '+%Y%m%d-%H%M%S-%N')-$$"

exec "$AM_DIR/.venv/bin/python" "$AM_DIR/__main__.py" "${WEX_TASK_ID}" "${@}"
