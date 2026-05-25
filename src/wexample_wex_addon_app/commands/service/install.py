from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option

from wexample_wex_addon_app.const.service import SERVICE_CONFIG_PROXY, SERVICE_TAG_DB
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


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
@as_sudo()
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Install a service into an app")
def app__service__install(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    service: str,
    force: bool = False,
) -> None:
    from wexample_helpers.helpers.string import string_to_snake_case

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

        config_file = app_workdir.get_config_file()
        config = config_file.read_config()

        if (
            not config.search(f"service.{normalized_service_name}").is_none()
            and not force_install
        ):
            context.io.log(
                f"Service '{normalized_service_name}' already installed, skipping"
            )
            return

        installing.add(normalized_service_name)
        try:
            manifest = app_addon_manager.get_service_manifest(normalized_service_name)
            for dependency in manifest.get("dependencies", []) or []:
                _install(service_name=dependency, force_install=False)

            config_file = app_workdir.get_config_file()
            config = config_file.read_config()

            config.set_by_path(f"service.{normalized_service_name}", {})

            if config.search("global.main_service").is_none():
                config.set_by_path("global.main_service", normalized_service_name)

            if (
                SERVICE_TAG_DB in (manifest.get("tags") or [])
                and config.search("docker.db.main").is_none()
            ):
                config.set_by_path("docker.db.main", normalized_service_name)

            if (manifest.get("config") or {}).get(SERVICE_CONFIG_PROXY):
                config.set_by_path("sidecar.proxy", {})

            config_file.write_config(config)
            app_workdir.get_runtime_config(rebuild=True)

            # Copy service samples into app — docker-compose.yml files are merged
            # (services: section) instead of overwritten, so installing a new service
            # never erases compose entries from previously installed services.
            for (
                inherited_service_name
            ) in app_addon_manager.get_service_inheritance_chain(
                normalized_service_name
            ):
                inherited_service_dir = app_addon_manager.find_service_dir(
                    inherited_service_name
                )
                if inherited_service_dir is None:
                    continue

                from wexample_app.const.globals import WORKDIR_SETUP_DIR
                from wexample_helpers.helpers.file import file_copytree_merge_yaml

                samples_dir = inherited_service_dir / "samples"
                if not samples_dir.is_dir():
                    continue

                app_setup_path = app_workdir.get_path() / WORKDIR_SETUP_DIR
                file_copytree_merge_yaml(
                    samples_dir,
                    app_setup_path,
                    merge_filenames=["docker-compose.yml"],
                    merge_keys=["services", "volumes", "networks"],
                    ignore_filenames=[".wex.yml"],
                )

            # Write vars declared in service.yml into env (skip if already present)
            from wexample_wex_addon_app.helpers.vars_declaration import (
                process_vars_declarations,
            )

            app_service = app_addon_manager.get_app_service(
                normalized_service_name, app_workdir
            )
            process_vars_declarations(
                vars_decl=app_service.get_vars(),
                app_workdir=app_workdir,
                io=context.io,
            )

            # Step 3: declarative install_config — write config.yml keys via Jinja2
            install_config = manifest.get("install_config") or {}
            if install_config:
                import secrets

                from jinja2 import Environment as JinjaEnv
                from wexample_helpers.helpers.string import string_random_token

                jinja = JinjaEnv()
                jinja.globals.update(
                    {
                        "token": string_random_token,
                        "hex": lambda n=32: secrets.token_hex(n),
                        "urlsafe": lambda n=24: secrets.token_urlsafe(n),
                    }
                )
                jinja_ctx = {
                    "name": normalized_service_name,
                    "app_name": app_workdir.get_config().search("global.name").get_str()
                    or "",
                    "env": app_workdir.get_app_env() or "prod",
                }

                config_file = app_workdir.get_config_file()
                config = config_file.read_config()
                changed = False

                for raw_key, raw_value in install_config.items():
                    rendered_key = jinja.from_string(str(raw_key)).render(jinja_ctx)
                    if not config.search(rendered_key).is_none():
                        continue
                    if isinstance(raw_value, str):
                        rendered_value: object = jinja.from_string(raw_value).render(
                            jinja_ctx
                        )
                    else:
                        rendered_value = raw_value
                    config.set_by_path(rendered_key, rendered_value)
                    changed = True

                if changed:
                    config_file.write_config(config)
                    app_workdir.get_runtime_config(rebuild=True)

            app_addon_manager.run_service_hook(
                hook="service/install",
                app_workdir=app_workdir,
            )

            from wexample_wex_addon_app.commands.state.rectify import (
                app__state__rectify,
            )

            context.kernel.run_function(
                app__state__rectify,
                {"yes": True, "loop": True},
            )

            context.io.log(f"Installed service '{normalized_service_name}'")
        finally:
            installing.remove(normalized_service_name)

    _install(service_name=service, force_install=force)
