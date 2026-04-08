from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Generate runtime config and docker-compose.runtime.yml")
def app__config__write(
        context: ExecutionContext,
        app_workdir: AppWorkdir,
) -> AbstractResponse:
    import socket

    from wexample_app.const.globals import WORKDIR_SETUP_DIR
    from wexample_app.response.queued_collection_response import QueuedCollectionResponse
    from wexample_config.config_value.nested_config_value import NestedConfigValue
    from wexample_helpers.helpers.dict import dict_merge
    from wexample_wex_core.const.globals import CORE_DIR_NAME_TMP

    app_path = app_workdir.get_path()
    env = app_workdir.get_app_env()
    name = app_workdir.get_project_name()
    project_name = f"{name}_{env}"
    tmp_dir = app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP

    def _runtime(previous_value=None) -> None:
        tmp_dir.mkdir(parents=True, exist_ok=True)

        app_config = app_workdir.get_runtime_app_config()
        domains_config = app_workdir.get_domains_config()

        merged = {
            "app": dict_merge(app_config, {
                "env": env,
                "name": name,
                "project_name": project_name,
                "host": {"ip": socket.gethostbyname(socket.gethostname())},
                "started": False,
                "path": str(app_path) + "/",
                "setup_path": str(app_path / WORKDIR_SETUP_DIR) + "/",
                **domains_config,
            }),
        }

        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        app_manager = AppAddonManager.from_kernel(context.kernel)
        services = app_manager.get_app_services(app_workdir)
        for app_service in services:
            contribution = app_service.get_runtime_contribution()
            merged = dict_merge(merged, contribution)

        hook_results = app_manager.run_service_hook(
            hook="runtime/contribution",
            app_workdir=app_workdir,
        )
        for hook_contribution in hook_results.values():
            if isinstance(hook_contribution, dict):
                merged = dict_merge(merged, hook_contribution)

        app_workdir.get_runtime_config_file().write_config(NestedConfigValue(raw=merged))
        context.io.log(f"Runtime config written ({len(services) - 1} service(s))")

    def _env(previous_value=None) -> None:
        from wexample_filestate.item.file.env_file import EnvFile

        def _flatten(data: dict, prefix: str = "") -> dict:
            result = {}
            for k, v in data.items():
                key = f"{prefix}_{k}".upper() if prefix else k.upper()
                if isinstance(v, dict):
                    result.update(_flatten(v, key))
                else:
                    result[key] = v
            return result

        # Load .env first (user-defined vars), runtime flattened on top (takes priority)
        dot_env = app_workdir.get_env_parameters().to_dict()
        runtime = app_workdir.get_runtime_config_file().read_config().to_dict()
        env_vars = {**dot_env, **_flatten(runtime)}

        docker_env_path = tmp_dir / "docker.env"
        env_file = EnvFile.create_from_path(path=docker_env_path, io=context.io)
        env_file.write_config(NestedConfigValue(raw=env_vars))
        context.io.log(f"docker.env written ({len(env_vars)} variable(s))")

    def _docker(previous_value=None) -> None:
        import subprocess

        import yaml as _yaml

        runtime = app_workdir.get_runtime_config_file().read_config().to_dict()
        docker_env_path = tmp_dir / "docker.env"
        compose_runtime_path = tmp_dir / "docker-compose.runtime.yml"

        compose_files = []

        # Base app compose
        base_compose = app_path / WORKDIR_SETUP_DIR / "docker" / "docker-compose.yml"
        if base_compose.exists():
            compose_files.append(str(base_compose))

        # Env-specific app compose
        env_compose = app_path / WORKDIR_SETUP_DIR / "env" / env / "docker" / "docker-compose.yml"
        if env_compose.exists():
            compose_files.append(str(env_compose))

        # Infrastructure-only service composes (networks, volumes — no services key)
        for service_data in runtime.get("service", {}).values():
            if not isinstance(service_data, dict) or "compose" not in service_data:
                continue
            compose_path = service_data["compose"]
            try:
                with open(compose_path) as f:
                    compose_content = _yaml.safe_load(f) or {}
                if "services" not in compose_content:
                    compose_files.append(compose_path)
            except (OSError, _yaml.YAMLError):
                pass

        # Per-service VIRTUAL_HOST override (Option A: from service.{name}.domains in config)
        main_service = runtime.get("app", {}).get("main_service") or runtime.get("global", {}).get("main_service")
        app_domains_string = runtime.get("app", {}).get("domains_string", "")
        domains_override: dict = {"services": {}}

        for service_name, service_data in runtime.get("service", {}).items():
            if not isinstance(service_data, dict):
                continue

            service_domains = service_data.get("domains")
            if service_domains:
                # Explicit per-service domains
                virtual_host = ",".join(service_domains) if isinstance(service_domains, list) else str(service_domains)
            elif service_name == main_service and app_domains_string:
                # Fallback: main_service inherits app-level domains
                virtual_host = app_domains_string
            else:
                continue

            container_name = f"{name}_{service_name}"
            domains_override["services"][container_name] = {
                "environment": {"VIRTUAL_HOST": virtual_host}
            }

        if domains_override["services"]:
            domains_override_path = tmp_dir / "docker-compose.domains.yml"
            domains_override_path.write_text(_yaml.dump(domains_override, default_flow_style=False))
            compose_files.append(str(domains_override_path))

        if not compose_files:
            context.io.log("No docker compose files found, skipping")
            return

        cmd = ["docker", "compose"]
        for f in compose_files:
            cmd += ["-f", f]
        cmd += [
            "--profile", f"env_{env}",
            "--project-name", project_name,
            "--env-file", str(docker_env_path),
            "config",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"docker compose config failed:\n{result.stderr}"
            )

        compose_runtime_path.write_text(result.stdout)
        context.io.log(f"docker-compose.runtime.yml written ({len(compose_files)} file(s))")

    return QueuedCollectionResponse(kernel=context.kernel, content=[
        _runtime,
        _env,
        _docker,
    ])
