from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Generate runtime config and docker-compose.runtime.yml",
)
def app__config__build(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    import socket

    from wexample_app.const.globals import WORKDIR_SETUP_DIR
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )
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
            "app": dict_merge(
                app_config,
                {
                    "env": env,
                    "name": name,
                    "project_name": project_name,
                    "host": {"ip": socket.gethostbyname(socket.gethostname())},
                    "started": False,
                    "path": str(app_path) + "/",
                    "setup_path": str(app_path / WORKDIR_SETUP_DIR) + "/",
                    **domains_config,
                },
            ),
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

        app_workdir.write_runtime_config(NestedConfigValue(raw=merged))
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

        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        net_check = subprocess.run(
            ["docker", "network", "inspect", "wex_net"],
            capture_output=True,
        )
        if net_check.returncode != 0:
            subprocess.run(["docker", "network", "create", "wex_net"], check=True)
            context.io.log("Created docker network: wex_net")

        app_manager = AppAddonManager.from_kernel(context.kernel)
        app_workdir.get_runtime_config_file().read_config().to_dict()
        docker_env_path = tmp_dir / "docker.env"
        compose_runtime_path = tmp_dir / "docker-compose.runtime.yml"

        compose_files = []

        # Check if any service in this app creates the docker network (tagged "network", e.g. proxy)
        creates_network = any(
            "network" in app_manager.get_service_manifest(s.name).get("tags", [])
            for s in app_manager.get_app_services(app_workdir)
            if s.name != "default"
        )

        # Include the base compose that either creates wex_net (proxy) or references it as external
        resources_dir = (
            AppAddonManager.get_package_source_path() / "resources" / "docker"
        )
        addon_base_compose = resources_dir / (
            "docker-compose.network.yml" if creates_network else "docker-compose.yml"
        )
        if addon_base_compose.exists():
            compose_files.append(str(addon_base_compose))

        # Samples addon compose files are NOT added to compose_files here.
        #
        # Each service declares a samples/docker/docker-compose.yml that is copied into
        # the app's .wex/docker/docker-compose.yml at service/install time. Those sample
        # entries use `extends: file: ${SERVICE_X_COMPOSE}` so Docker Compose resolves
        # them directly via env-var path — no need to list the base compose with -f.
        #
        # Adding base service composes to -f would duplicate services: if the app names
        # its service differently from the addon (e.g. drive_maria vs maria), both would
        # appear in the merged compose with the same container_name, causing a conflict.
        #
        # If you are tempted to re-add service composes here to fix missing containers,
        # the real fix is to add a samples/docker/docker-compose.yml to the service addon
        # with the appropriate extends entries — not to patch this function.
        # Base app compose
        base_compose = app_path / WORKDIR_SETUP_DIR / "docker" / "docker-compose.yml"
        if base_compose.exists():
            compose_files.append(str(base_compose))

        # Env-specific app compose — highest priority, overrides everything above
        env_compose = (
            app_path / WORKDIR_SETUP_DIR / "env" / env / "docker" / "docker-compose.yml"
        )
        if env_compose.exists():
            compose_files.append(str(env_compose))

        if not compose_files:
            context.io.log("No docker compose files found, skipping")
            return

        cmd = ["docker", "compose"]
        for f in compose_files:
            cmd += ["-f", f]
        cmd += [
            "--profile",
            f"env_{env}",
            "--project-name",
            project_name,
            "--env-file",
            str(docker_env_path),
            "config",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"docker compose config failed:\n{result.stderr}")

        compose_runtime_path.write_text(result.stdout)
        context.io.log(
            f"docker-compose.runtime.yml written ({len(compose_files)} file(s))"
        )

        import yaml

        compose_data = yaml.safe_load(result.stdout)
        services = compose_data.get("services", {})
        host_paths_map = {}
        if services:
            first_service = next(iter(services.values()))
            for vol in first_service.get("volumes", []):
                if isinstance(vol, dict) and vol.get("type") == "bind":
                    source = vol.get("source", "")
                    target = vol.get("target", "")
                    if source.endswith("/"):
                        host_paths_map[target + "/"] = source
        app_workdir.set_local_data("debug", {"host_paths_map": host_paths_map})
        context.io.log(f"debug.yml written ({len(host_paths_map)} path(s))")

    return QueuedCollectionResponse(
        kernel=context.kernel,
        content=[
            _runtime,
            _env,
            _docker,
        ],
    )
