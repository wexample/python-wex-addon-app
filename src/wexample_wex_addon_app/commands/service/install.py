from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.const.service import SERVICE_CONFIG_PROXY, SERVICE_TAG_DB
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

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
                config.set_by_path("helper.proxy", {})

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
                from wexample_helpers.helpers.file import file_copytree_as_real_user

                samples_dir = inherited_service_dir / "samples"
                if not samples_dir.is_dir():
                    continue

                app_setup_path = app_workdir.get_path() / WORKDIR_SETUP_DIR

                # Merge docker-compose.yml files rather than overwriting
                import yaml
                from pathlib import Path

                for src_compose in samples_dir.rglob("docker-compose.yml"):
                    rel = src_compose.relative_to(samples_dir)
                    dst_compose = app_setup_path / rel

                    if dst_compose.exists():
                        existing = yaml.safe_load(dst_compose.read_text()) or {}
                        incoming = yaml.safe_load(src_compose.read_text()) or {}

                        for top_key in ("services", "volumes", "networks"):
                            if top_key in incoming:
                                existing.setdefault(top_key, {})
                                # Incoming entries win if key already present
                                existing[top_key].update(incoming[top_key])

                        import os
                        from wexample_helpers.helpers.user import user_get_real_uid, user_get_real_gid
                        dst_compose.write_text(yaml.dump(existing, default_flow_style=False, allow_unicode=True))
                        os.chown(dst_compose, user_get_real_uid(), user_get_real_gid())
                        continue

                    # File doesn't exist yet — use normal copy for this one file
                    dst_compose.parent.mkdir(parents=True, exist_ok=True)
                    import shutil, os
                    from wexample_helpers.helpers.user import user_get_real_uid, user_get_real_gid
                    shutil.copy2(src_compose, dst_compose)
                    os.chown(dst_compose, user_get_real_uid(), user_get_real_gid())

                # Copy all non-compose files normally
                non_compose = [f for f in samples_dir.rglob("*") if f.is_file() and f.name != "docker-compose.yml"]
                if non_compose:
                    import shutil, os
                    from wexample_helpers.helpers.user import user_get_real_uid, user_get_real_gid
                    uid, gid = user_get_real_uid(), user_get_real_gid()
                    for src_file in non_compose:
                        rel = src_file.relative_to(samples_dir)
                        dst_file = app_setup_path / rel
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        os.chown(dst_file, uid, gid)

            # Write vars declared in service.yml into .env (skip if already present)
            app_service = app_addon_manager.get_app_service(
                normalized_service_name, app_workdir
            )
            service_vars = app_service.get_vars()
            env_file = app_workdir.get_path() / ".wex" / ".env"
            existing_env = env_file.read_text() if env_file.exists() else ""

            # Step 1: non-required defaults (write silently, no prompt)
            defaults_to_write = {
                key: str(meta["default"])
                for key, meta in service_vars.items()
                if "default" in meta
                and not meta.get("generated")
                and not meta.get("required")
            }
            if defaults_to_write:
                from wexample_helpers.helpers.file import file_env_append_as_real_user

                file_env_append_as_real_user(env_file, defaults_to_write)
                existing_env = env_file.read_text()

            # Step 2: required vars — prompt (with optional pre-fill from default)
            for key, meta in service_vars.items():
                if meta.get("generated"):
                    continue
                if not meta.get("required"):
                    continue
                if f"{key}=" in existing_env:
                    continue

                description = meta.get("description", "")
                question = f"{key}" + (f" — {description}" if description else "")
                suggested = str(meta["default"]) if "default" in meta else None

                value = None
                while not value:
                    if value is not None:
                        context.io.log(f"  '{key}' is required, please enter a value.")
                    response = context.io.input(
                        question=question, default_value=suggested
                    )
                    value = response.get_value()

                from wexample_helpers.helpers.file import file_env_append_as_real_user

                file_env_append_as_real_user(env_file, {key: value})
                existing_env = env_file.read_text()

            app_addon_manager.run_service_hook(
                hook="service/install",
                app_workdir=app_workdir,
            )

            from wexample_wex_addon_app.commands.file_state.rectify import (
                app__file_state__rectify,
            )

            context.kernel.run_function(
                app__file_state__rectify,
                {"yes": True},
            )

            context.io.log(f"Installed service '{normalized_service_name}'")
        finally:
            installing.remove(normalized_service_name)

    _install(service_name=service, force_install=force)
