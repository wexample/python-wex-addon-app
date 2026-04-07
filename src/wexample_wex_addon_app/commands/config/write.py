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
        """Generate docker.env — v5 names kept for compat, v6 aliases added alongside.
        v6: todo — migration: supprimer les noms v5 quand toutes les apps seront migrées
        """
        # v6: todo — injecter user/group/uid/gid (bloqué par helpers user/group)
        # v6: todo — injecter domains, domain_tld (bloqué par config domaines)

        app_config = app_workdir.get_config()
        setup_path = f"{app_path / WORKDIR_SETUP_DIR}/"

        lines = [
            # v5 names (used by existing app compose files)
            f"GLOBAL_NAME={name}",
            f"RUNTIME_NAME={project_name}",
            f"RUNTIME_PATH_APP={app_path}/",
            f"RUNTIME_PATH_APP_ENV={setup_path}",
            # v6 aliases — v6: todo migration: remplacer les v5 ci-dessus par ceux-ci
            f"APP_NAME={name}",
            f"APP_ENV={env}",
            f"APP_PROJECT={project_name}",
            f"APP_PATH={app_path}/",
            f"APP_SETUP_PATH={setup_path}",
        ]

        # Vendor path
        vendor_path = app_config.search("global.vendor_local_path").get_str_or_none()
        if vendor_path:
            lines.append(f"VENDOR_LOCAL_PATH={vendor_path}")

        # Bind paths from runtime config → RUNTIME_BIND_* (v5) + BIND_* (v6)
        # v6: todo migration: remplacer RUNTIME_BIND_* par BIND_* dans les compose apps
        runtime_config = app_workdir.get_runtime_config()
        bind_config = runtime_config.search("bind")
        if not bind_config.is_none():
            for bind_key, bind_value in bind_config.to_dict().items():
                key_upper = bind_key.upper()
                lines.append(f"RUNTIME_BIND_{key_upper}={bind_value}")
                lines.append(f"BIND_{key_upper}={bind_value}")

        # Per-service variables
        services = context.middleware.get_services(app_workdir, kernel=context.kernel)
        for app_service in services:
            sname = app_service.name.upper()
            sconfig = app_config.search(f"service.{app_service.name}")
            sconfig_dict = sconfig.to_dict() if not sconfig.is_none() else {}

            compose = app_service.get_compose_file()
            if compose:
                # v5 name + v6 alias
                # v6: todo migration: remplacer RUNTIME_SERVICE_*_YML_ENV par SERVICE_*_COMPOSE
                lines.append(f"RUNTIME_SERVICE_{sname}_YML_BASE={compose}")
                lines.append(f"RUNTIME_SERVICE_{sname}_YML_ENV={compose}")
                lines.append(f"SERVICE_{sname}_COMPOSE={compose}")

            for key, value in sconfig_dict.items():
                if key in ("v5_compose",):
                    continue
                # v5: SERVICE_MYSQL_NAME = DB name (confusingly named)
                # v6: SERVICE_MYSQL_DB   = DB name (explicit)
                # v6: todo migration: remplacer SERVICE_*_NAME par SERVICE_*_DB dans les compose services
                if key == "name":
                    lines.append(f"SERVICE_{sname}_NAME={value}")
                    lines.append(f"SERVICE_{sname}_DB={value}")
                else:
                    lines.append(f"SERVICE_{sname}_{key.upper()}={value}")

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
