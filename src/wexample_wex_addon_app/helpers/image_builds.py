from __future__ import annotations

from pathlib import Path

import yaml

from wexample_app.const.globals import APP_FILE_APP_CONFIG, WORKDIR_SETUP_DIR


def load_builds(app_path: Path) -> dict:
    config_file = app_path / WORKDIR_SETUP_DIR / APP_FILE_APP_CONFIG
    if not config_file.exists():
        raise FileNotFoundError(f"No config.yml found at {config_file}")
    with open(config_file) as f:
        data = yaml.safe_load(f) or {}
    images = data.get("docker", {}).get("images", {})
    if not images:
        raise KeyError(f"No docker.images section found in {WORKDIR_SETUP_DIR}/config.yml")
    return images


def resolve_build_order(builds: dict, name: str | None = None) -> list[str]:
    """Return build names in topological order (deps first).

    If name is given, returns only that build plus its transitive dependencies.
    """
    if name is not None:
        if name not in builds:
            raise KeyError(f"Build '{name}' not found in docker.images config")
        targets = _collect_deps(builds, name)
    else:
        targets = set(builds.keys())

    return _topo_sort(builds, targets)


def _collect_deps(builds: dict, name: str, visited: set | None = None) -> set[str]:
    if visited is None:
        visited = set()
    if name in visited:
        return visited
    visited.add(name)
    dep = builds[name].get("depends_on")
    if dep:
        _collect_deps(builds, dep, visited)
    return visited


def _topo_sort(builds: dict, targets: set[str]) -> list[str]:
    order: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        dep = builds.get(node, {}).get("depends_on")
        if dep and dep in targets:
            visit(dep)
        order.append(node)

    for node in builds:
        if node in targets:
            visit(node)

    return order
