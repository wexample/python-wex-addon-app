from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@option(
    name="service",
    short_name="s",
    type=str,
    required=True,
    description="Service name to install",
)
@option(
    name="force",
    short_name="f",
    type=bool,
    is_flag=True,
    required=False,
    description="Install even if the service already exists in config.yml",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Install a service into an app")
def app__service__install(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    service: str,
    force: bool = False,
) -> None:
    from wexample_helpers.helpers.string import string_to_snake_case
    from wexample_helpers_yaml.helpers.yaml_helpers import yaml_read

    from wexample_wex_addon_app.app_addon_manager import AppAddonManager

    app_addon_manager = AppAddonManager.from_kernel(context.kernel)
    installing: set[str] = set()

    def _install(service_name: str, force_install: bool) -> None:
        normalized_service_name = string_to_snake_case(service_name)
        service_dir = app_addon_manager.find_service_dir(normalized_service_name)

        if service_dir is None:
            raise ValueError(f"Unknown service '{normalized_service_name}'")

        if normalized_service_name in installing:
            raise ValueError(
                f"Cyclic service dependency detected while installing '{normalized_service_name}'"
            )

        installing.add(normalized_service_name)
        try:
            manifest = yaml_read(file_path=str(service_dir / "service.yml"), default={}) or {}
            for dependency in manifest.get("dependencies", []) or []:
                _install(service_name=dependency, force_install=False)

            config_file = app_workdir.get_config_file()
            config = config_file.read_config()
            service_config = config.search(f"service.{normalized_service_name}")

            if not service_config.is_none() and not force_install:
                context.io.log(f"Service '{normalized_service_name}' already installed")
                return

            config.set_by_path(f"service.{normalized_service_name}", {})

            if config.search("global.main_service").is_none():
                config.set_by_path("global.main_service", normalized_service_name)

            if (
                normalized_service_name in app_addon_manager.find_services_by_tag("db")
                and config.search("docker.db.main").is_none()
            ):
                config.set_by_path("docker.db.main", normalized_service_name)

            config_file.write_config(config)
            app_workdir.get_runtime_config(rebuild=True)

            app_addon_manager.run_service_hook(
                hook="service/install",
                app_workdir=app_workdir,
                arguments={"service": normalized_service_name},
            )

            context.io.log(f"Installed service '{normalized_service_name}'")
        finally:
            installing.remove(normalized_service_name)

    _install(service_name=service, force_install=force)
