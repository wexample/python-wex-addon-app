from __future__ import annotations

from pathlib import Path

import yaml

BUILDS_FILE = ".wex/docker/builds.yml"


def load_builds(app_path: Path) -> dict:
    builds_file = app_path / BUILDS_FILE
    if not builds_file.exists():
        raise FileNotFoundError(f"No builds.yml found at {builds_file}")
    with open(builds_file) as f:
        data = yaml.safe_load(f) or {}
    return data.get("builds", {})


def resolve_build_order(builds: dict, name: str | None = None) -> list[str]:
    """Return build names in topological order (deps first).

    If name is given, returns only that build plus its transitive dependencies.
    """
    if name is not None:
        if name not in builds:
            raise KeyError(f"Build '{name}' not found in builds.yml")
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
