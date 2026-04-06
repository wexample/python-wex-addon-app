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
    from wexample_app.response.queued_collection_response import QueuedCollectionResponse

    def _runtime(previous_value=None) -> None:
        import socket

        from wexample_helpers.helpers.dict import dict_merge

        # v6: todo — injecter user/group/uid/gid dans le runtime config (bloqué par helpers user/group)
        # v6: todo — injecter données services via hook config/write-runtime (bloqué par migration services)
        # v6: todo — injecter domains, domain_tld, domains_string (bloqué par config domaines)

        env = app_workdir.get_app_env()
        name = app_workdir.get_project_name()

        extra = {
            "env": env,
            "name": f"{name}_{env}",
            "host": {"ip": socket.gethostbyname(socket.gethostname())},
            "started": False,
        }

        from wexample_config.config_value.nested_config_value import NestedConfigValue

        base = app_workdir.build_runtime_config_value().to_dict()
        merged = dict_merge(base, extra)

        app_workdir.get_runtime_config_file().write_config(NestedConfigValue(raw=merged))

        context.io.log("Runtime config written")

    def _docker(previous_value=None) -> None:
        import subprocess

        from wexample_app.const.globals import WORKDIR_SETUP_DIR
        from wexample_wex_core.const.globals import CORE_DIR_NAME_TMP

        app_path = app_workdir.get_path()
        env = app_workdir.get_app_env()

        # Collect compose files
        compose_files = []

        # Inject default wex network compose (defines wex_net external network)
        # v6: todo — conditionnel selon docker.has_default_network (actuellement toujours injecté)
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager
        network_compose = AppAddonManager.get_package_source_path() / "resources" / "docker" / "docker-compose.network.yml"
        if network_compose.exists():
            compose_files.append(str(network_compose))

        # Inject service compose files declared in service.yml (docker.compose)
        from wexample_helpers_yaml.helpers.yaml_helpers import yaml_read
        from wexample_wex_addon_app.resolver.service_command_resolver import ServiceCommandResolver

        app_config = app_workdir.get_config()
        app_services = app_config.search("service").to_dict() if not app_config.search("service").is_none() else {}

        service_resolver = next(
            (r for r in context.kernel.get_resolvers() if isinstance(r, ServiceCommandResolver)),
            None,
        )
        if service_resolver:
            for service_name in app_services:
                service_dir = service_resolver._find_service_dir(service_name)
                if not service_dir:
                    continue
                service_manifest = yaml_read(file_path=str(service_dir / "service.yml"), default={})
                compose_rel = service_manifest.get("docker", {}).get("compose")
                if compose_rel:
                    compose_abs = service_dir / compose_rel
                    if compose_abs.exists():
                        compose_files.append(str(compose_abs))

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

        docker_env_file = app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / "docker.env"
        project_name = app_workdir.get_project_name() + "_" + app_workdir.get_app_env()

        cmd = ["docker", "compose"]
        for f in compose_files:
            cmd += ["-f", f]
        cmd += [
            "--project-name", project_name,
        ]
        if docker_env_file.exists():
            cmd += ["--env-file", str(docker_env_file)]
        cmd += ["config"]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(app_path))

        if result.returncode != 0:
            raise RuntimeError(f"docker compose config failed:\n{result.stderr}")

        runtime_compose = (
            app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / "docker-compose.runtime.yml"
        )
        runtime_compose.write_text(result.stdout)

        context.io.log(f"docker-compose.runtime.yml written")

    return QueuedCollectionResponse(kernel=context.kernel, content=[_runtime, _docker])
