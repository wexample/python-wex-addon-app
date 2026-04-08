from __future__ import annotations

from pathlib import Path


def get_helper_app_path(name: str, env: str) -> Path:
    return Path(f"/var/www/{env}/wex-{name}")
