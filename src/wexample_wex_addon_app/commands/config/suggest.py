from __future__ import annotations

import re
from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


_VAR_REF_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::-([^}]*))?\}")

# Built-ins injected by wex at runtime — never declared by the user.
_WEX_BUILTINS = {
    "APP_BRANCH",
    "APP_DOMAIN",
    "APP_DOMAINS_STRING",
    "APP_ENV",
    "APP_NAME",
    "APP_PATH",
    "APP_PROJECT_NAME",
    "APP_SETUP_PATH",
    "BIND_WEB_APACHE_CONF",
    "RUNTIME_BIND_WEB_PHP_INI",
}
_WEX_BUILTIN_PREFIXES = ("SERVICE_",)


@option(
    name="apply",
    type=bool,
    is_flag=True,
    default=False,
    description="Write the suggestions into .wex/config.yml (default: dry-run, only print)",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description=(
        "Scan docker-compose for ${VAR} references and suggest declarations "
        "for .wex/config.yml → vars: (built-ins and already-declared vars skipped). "
        "Also best-effort DNS-resolves the first domain of each env's config.yml "
        "and proposes filling `remotes[].host` when missing."
    ),
)
def app__config__suggest(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    apply: bool = False,
) -> None:
    from wexample_app.const.globals import APP_PATH_DOCKER_COMPOSE

    _suggest_remotes(context, app_workdir, apply=apply)

    compose_path = app_workdir.get_path() / APP_PATH_DOCKER_COMPOSE
    if not compose_path.exists():
        context.io.warning(f"No docker-compose at {compose_path}")
        return

    found = _scan_compose(compose_path)
    if not found:
        context.io.success("No ${VAR} references in docker-compose")
        return

    declared = _read_declared_vars(app_workdir)
    existing_env = app_workdir.get_env_parameters().to_dict()

    to_suggest = {
        name: default
        for name, default in found.items()
        if not _is_builtin(name) and name not in declared
    }

    if not to_suggest:
        context.io.success("All non-builtin vars are already declared in vars:")
        return

    suggestions = {}
    for name in sorted(to_suggest):
        default = to_suggest[name]
        entry: dict = {"description": ""}
        if default is not None:
            entry["default"] = default
        else:
            entry["required"] = True
        suggestions[name] = entry

    if not apply:
        import yaml

        snippet = yaml.safe_dump({"vars": suggestions}, sort_keys=False)
        context.io.log(
            f"{len(suggestions)} suggested var(s) — dry-run, use --apply to write:\n\n"
            + snippet
            + "\n# Currently set values in .wex/local/env.yml (for reference):"
        )
        for name in sorted(to_suggest):
            current = existing_env.get(name)
            if current is not None:
                context.io.log(f"#   {name} = {current!r}")
        return

    # Apply: merge into config.yml → vars: without touching anything else
    config_file = app_workdir.get_config_file()
    config = config_file.read_parsed() or {}
    if not isinstance(config, dict):
        context.io.error("config.yml is not a mapping — aborting")
        return

    existing_vars = config.get("vars") if isinstance(config.get("vars"), dict) else {}
    merged_vars = {**existing_vars}
    for name, entry in suggestions.items():
        merged_vars.setdefault(name, entry)
    config["vars"] = merged_vars

    config_file.write_parsed(config)
    context.io.success(
        f"Added {len(suggestions)} var(s) to .wex/config.yml → vars:. "
        "Fill in the `description:` fields before committing."
    )


def _is_builtin(name: str) -> bool:
    return name in _WEX_BUILTINS or any(
        name.startswith(p) for p in _WEX_BUILTIN_PREFIXES
    )


def _read_declared_vars(app_workdir) -> set[str]:
    decl = app_workdir.get_config().search("vars").to_dict_or_none() or {}
    return set(decl.keys())


def _scan_compose(compose_path) -> dict[str, str | None]:
    text = compose_path.read_text(encoding="utf-8")
    found: dict[str, str | None] = {}
    for match in _VAR_REF_PATTERN.finditer(text):
        name, default = match.group(1), match.group(2)
        if name not in found or default:
            found[name] = default
    return found


def _resolve_domain_best_effort(domain: str, timeout_s: float = 2.0) -> str | None:
    """DNS-resolve `domain` to an IPv4 in <= timeout_s. Returns None on
    failure (NXDOMAIN, timeout, local-only TLD, anything). No retries, no
    fancy resolvers — this is "if available" comfort, not a hard contract."""
    import socket
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeoutError

    def _lookup() -> str | None:
        try:
            return socket.gethostbyname(domain)
        except (socket.gaierror, OSError):
            return None

    with ThreadPoolExecutor(max_workers=1) as ex:
        try:
            return ex.submit(_lookup).result(timeout=timeout_s)
        except FutTimeoutError:
            return None


def _has_filled_host(remotes) -> bool:
    if not isinstance(remotes, list) or not remotes:
        return False
    first = remotes[0]
    if not isinstance(first, dict):
        return False
    host = first.get("host")
    return isinstance(host, str) and bool(host.strip())


def _suggest_remotes(context, app_workdir, apply: bool) -> None:
    """Best-effort: when an env config has a `domains:` (or `domain:`) entry
    but no usable `remotes[].host`, try resolving the first domain in DNS and
    fill it in. Silent skip on any DNS failure — we don't try hard."""
    import yaml

    env_dir = app_workdir.get_path() / ".wex" / "env"
    if not env_dir.is_dir():
        return

    candidates: list[tuple[str, "Path", str, str]] = []  # (env_name, path, domain, ip)
    for env_config_path in sorted(env_dir.glob("*/config.yml")):
        env_name = env_config_path.parent.name
        try:
            data = yaml.safe_load(env_config_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            context.io.warning(f"Skipping {env_config_path}: {e}")
            continue
        if not isinstance(data, dict):
            continue
        if _has_filled_host(data.get("remotes")):
            continue

        domains = data.get("domains") or (
            [data["domain"]] if isinstance(data.get("domain"), str) else []
        )
        first = next(
            (d.strip() for d in domains if isinstance(d, str) and d.strip()), None
        )
        if not first:
            continue

        ip = _resolve_domain_best_effort(first)
        if not ip:
            continue

        candidates.append((env_name, env_config_path, first, ip))

    if not candidates:
        return

    if not apply:
        context.io.log(
            f"Found {len(candidates)} DNS-resolvable env(s) without `remotes[].host`. "
            "Dry-run, use --apply to fill:"
        )
        for env_name, _, domain, ip in candidates:
            context.io.log(f"  - {env_name}: {domain} → {ip}", indentation=1)
        return

    for env_name, path, domain, ip in candidates:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            continue
        data["remotes"] = [{"name": "main", "host": ip}]
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        context.io.success(
            f"Set remotes[main].host = {ip} (resolved from {domain}) "
            f"in .wex/env/{env_name}/config.yml"
        )


