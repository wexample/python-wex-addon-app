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

        # Merge base config + env-specific override (env/local/config.yml)
        app_config = dict_merge(
            app_workdir.get_config().to_dict(),
            app_workdir.get_config(env_name=env).to_dict_or_none() or {},
        )

        # Flatten env-specific block into root if present (v5 compat: env.local.* → root)
        env_block = app_config.pop("env", {})
        app_config.update(env_block.get(env, {}))

        merged = {
            "app": dict_merge(app_config, {
                "env": env,
                "name": name,
                "project_name": project_name,
                "host": {"ip": socket.gethostbyname(socket.gethostname())},
                "started": False,
                "path": str(app_path) + "/",
                "setup_path": str(app_path / WORKDIR_SETUP_DIR) + "/",
            }),
        }

        services = context.middleware.get_services(app_workdir, kernel=context.kernel)
        for app_service in services:
            contribution = app_service.get_runtime_contribution()
            merged = dict_merge(merged, contribution)

        hook_results = context.middleware.call_service_hook(
            hook="runtime/contribution",
            services=services,
            kernel=context.kernel,
            app_path=str(app_path),
        )
        for hook_contribution in hook_results.values():
            if isinstance(hook_contribution, dict):
                merged = dict_merge(merged, hook_contribution)

        app_workdir.get_runtime_config_file().write_config(NestedConfigValue(raw=merged))
        context.io.log(f"Runtime config written ({len(services)} service(s))")

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
        import yaml as _yaml
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
