from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@option(
    name="user",
    type=str,
    required=False,
    description="Owner of application files",
)
@option(
    name="group",
    type=str,
    required=False,
    description="Group of application files",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Generate runtime config and docker-compose.runtime.yml")
def app__config__write(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    user: str | None = None,
    group: str | None = None,
) -> AbstractResponse:
    from wexample_app.const.globals import WORKDIR_SETUP_DIR
    from wexample_app.response.queued_collection_response import QueuedCollectionResponse
    from wexample_wex_core.const.globals import CORE_DIR_NAME_TMP

    app_path = app_workdir.get_path()
    env = app_workdir.get_app_env()
    name = app_workdir.get_project_name()
    project_name = f"{name}_{env}"
    tmp_dir = app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP

    def _runtime(previous_value=None) -> None:
        import socket

        from wexample_helpers.helpers.dict import dict_merge

        # v6: todo — injecter user/group/uid/gid dans le runtime config (bloqué par helpers user/group)
        # v6: todo — injecter domains, domain_tld, domains_string (bloqué par config domaines)

        extra = {
            "env": env,
            "name": project_name,
            "host": {"ip": socket.gethostbyname(socket.gethostname())},
            "started": False,
        }

        from wexample_config.config_value.nested_config_value import NestedConfigValue

        base = app_workdir.build_runtime_config_value().to_dict()
        merged = dict_merge(base, extra)

        app_workdir.get_runtime_config_file().write_config(NestedConfigValue(raw=merged))

        context.io.log("Runtime config written")

    def _env(previous_value=None) -> None:
        """Generate docker.env with v6 naming convention."""
        # v6: todo — injecter user/group/uid/gid (bloqué par helpers user/group)
        # v6: todo — injecter domains, domain_tld (bloqué par config domaines)
        # v6: todo — migration des compose apps v5 pour utiliser APP_PROJECT, APP_SETUP_PATH, etc.

        app_config = app_workdir.get_config()

        lines = [
            f"APP_NAME={name}",
            f"APP_ENV={env}",
            f"APP_PROJECT={project_name}",
            f"APP_PATH={app_path}/",
            f"APP_SETUP_PATH={app_path / WORKDIR_SETUP_DIR}/",
            # Backward compat aliases for v5 user compose files
            f"GLOBAL_NAME={name}",
            f"RUNTIME_NAME={project_name}",
            f"RUNTIME_PATH_APP={app_path}/",
            f"RUNTIME_PATH_APP_ENV={app_path / WORKDIR_SETUP_DIR}/",
        ]

        # Vendor path (from config.yml if present)
        vendor_path = app_config.search("global.vendor_local_path").get_str_or_none()
        if vendor_path:
            lines.append(f"VENDOR_LOCAL_PATH={vendor_path}")

        # Bind paths from runtime config (bind.*) → RUNTIME_BIND_* for backward compat
        runtime_config = app_workdir.get_runtime_config()
        bind_config = runtime_config.search("bind")
        if not bind_config.is_none():
            for bind_key, bind_value in bind_config.to_dict().items():
                env_key = bind_key.upper()
                lines.append(f"RUNTIME_BIND_{env_key}={bind_value}")

        # Per-service variables
        services = context.middleware.get_services(app_workdir, kernel=context.kernel)
        for app_service in services:
            sname = app_service.name.upper()
            sconfig = app_config.search(f"service.{app_service.name}").to_dict() if not app_config.search(f"service.{app_service.name}").is_none() else {}

            # Compose file path (v6 name + v5 backward compat)
            compose = app_service.get_compose_file()
            if not compose:
                # v6: todo — fallback v5 path à supprimer quand tous les services auront leur package v6
                v5_base = app_config.search(f"service.{app_service.name}.v5_compose").get_str_or_none()
                if v5_base:
                    compose_str = v5_base
                    lines.append(f"SERVICE_{sname}_COMPOSE={compose_str}")
                    lines.append(f"RUNTIME_SERVICE_{sname}_YML_BASE={compose_str}")
                    lines.append(f"RUNTIME_SERVICE_{sname}_YML_ENV={compose_str}")
            else:
                lines.append(f"SERVICE_{sname}_COMPOSE={compose}")
                # v5 backward compat
                lines.append(f"RUNTIME_SERVICE_{sname}_YML_BASE={compose}")
                lines.append(f"RUNTIME_SERVICE_{sname}_YML_ENV={compose}")

            # Service credentials
            for key, value in sconfig.items():
                env_key = f"SERVICE_{sname}_{key.upper()}"
                # v6: DB name uses _DB suffix (was _NAME in v5, confusing with service name)
                if key == "name":
                    lines.append(f"SERVICE_{sname}_DB={value}")
                    lines.append(f"SERVICE_{sname}_NAME={value}")  # v5 compat
                else:
                    lines.append(f"{env_key}={value}")

        docker_env_file = tmp_dir / "docker.env"
        docker_env_file.write_text("\n".join(lines) + "\n")
        context.io.log(f"docker.env written ({len(services)} service(s))")

    def _docker(previous_value=None) -> None:
        import subprocess

        # Collect compose files
        compose_files = []

        # Inject default wex network compose (defines wex_net external network)
        # v6: todo — conditionnel selon docker.has_default_network (actuellement toujours injecté)
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager
        network_compose = AppAddonManager.get_package_source_path() / "resources" / "docker" / "docker-compose.network.yml"
        if network_compose.exists():
            compose_files.append(str(network_compose))

        # Inject service compose files declared in service.yml (docker.compose)
        for app_service in context.middleware.get_services(app_workdir, kernel=context.kernel):
            compose = app_service.get_compose_file()
            if compose:
                compose_files.append(str(compose))

        base_compose = app_path / WORKDIR_SETUP_DIR / "docker" / "docker-compose.yml"
        if base_compose.exists():
            compose_files.append(str(base_compose))

        env_compose = app_path / WORKDIR_SETUP_DIR / "docker" / f"docker-compose.{env}.yml"
        if env_compose.exists():
            compose_files.append(str(env_compose))

        if not compose_files:
            context.io.log("No docker compose file found")
            return

        context.io.log(f"Compiling docker compose from {len(compose_files)} file(s)...")

        docker_env_file = tmp_dir / "docker.env"
        cmd = ["docker", "compose"]
        for f in compose_files:
            cmd += ["-f", f]
        cmd += ["--project-name", project_name]
        if docker_env_file.exists():
            cmd += ["--env-file", str(docker_env_file)]
        cmd += ["config"]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(app_path))

        if result.returncode != 0:
            raise RuntimeError(f"docker compose config failed:\n{result.stderr}")

        runtime_compose = tmp_dir / "docker-compose.runtime.yml"
        runtime_compose.write_text(result.stdout)
        context.io.log("docker-compose.runtime.yml written")

    return QueuedCollectionResponse(kernel=context.kernel, content=[_runtime, _env, _docker])
