from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from wexample_app.const.globals import APP_PATH_APP_MANAGER
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_app.resolver.abstract_command_resolver import AbstractCommandResolver
    from wexample_helpers.const.types import PathOrString
    from wexample_wex_core.middleware.abstract_middleware import AbstractMiddleware

    from wexample_wex_addon_app.service.app_service import AppService
    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@base_class
class AppAddonManager(AbstractAddonManager):
    @classmethod
    def get_package_module(cls) -> Any:
        import wexample_wex_addon_app

        return wexample_wex_addon_app

    @classmethod
    def get_shell_manager_path(cls) -> Path:
        from wexample_app.const.globals import APP_FILE_APP_MANAGER

        return (
            cls.get_package_source_path() / "resources" / f"{APP_FILE_APP_MANAGER}.sh"
        )

    def create_app_workdir(self, path: PathOrString | None = None) -> AppWorkdir | None:
        from pathlib import Path

        from wexample_helpers.helpers.cli import cli_make_clickable_path
        from wexample_helpers.helpers.module import module_load_class_from_file

        from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir

        app_path = (
            Path(path) if path is not None else self.kernel.call_workdir.get_path()
        )

        if not AppWorkdir.is_app_workdir_path(path=app_path):
            self.kernel.warning(
                f"Path does not match with an application directory structure: {cli_make_clickable_path(app_path)}"
            )
            return None

        custom_app_workdir_class_path = (
            app_path / APP_PATH_APP_MANAGER / "app_workdir.py"
        )
        if custom_app_workdir_class_path.exists():
            app_workdir_class = module_load_class_from_file(
                file_path=custom_app_workdir_class_path, class_name=AppWorkdir.__name__
            )
        else:
            app_workdir_class = AppWorkdir

        return app_workdir_class.create_from_path(
            path=app_path.resolve(),
            parent_io_handler=self.kernel,
        )

    @classmethod
    def from_kernel(cls, kernel) -> AppAddonManager:
        for addon in kernel.get_addons().values():
            if isinstance(addon, cls):
                return addon
        raise RuntimeError("AppAddonManager not registered in kernel")

    def get_app_services(self, app_workdir: AppWorkdir) -> list[AppService]:
        from wexample_wex_addon_app.service.app_service import AppService

        def _make_service(service_name: str) -> AppService:
            service_dir = self.find_service_dir(service_name)
            manifest = self.get_service_manifest(service_name) if service_dir else {}
            return AppService(
                name=service_name,
                app_workdir=app_workdir,
                addon_manager=self,
                service_dir=service_dir,
                manifest=manifest,
            )

        # "default" is always injected first — provides base compose (stdin_open, tty, restart, network)
        result = [_make_service("default")]

        services_config = app_workdir.get_config().search("service")
        if not services_config.is_none():
            for service_name in services_config.to_dict():
                result.append(_make_service(service_name))

        return result

    def run_service_hook(
        self,
        hook: str,
        app_workdir: AppWorkdir,
        arguments: dict | None = None,
    ) -> dict[str, Any]:
        """Call a hook on each service that declares it, return merged results.

        Hook name follows the command path convention: ``group/name`` (e.g. ``service/ready``).
        Services that do not declare the hook are silently skipped.
        """
        from pathlib import Path

        from wexample_app.const.output import OUTPUT_TARGET_NONE
        from wexample_helpers.helpers.string import string_to_snake_case
        from wexample_wex_core.common.command_request import CommandRequest

        results: dict[str, Any] = {}
        for service in self.get_app_services(app_workdir):
            if not service.service_dir:
                continue

            parts = hook.split("/")
            group_path = Path(*parts[:-1]) if len(parts) > 1 else Path()
            cmd_path = (
                service.service_dir
                / "commands"
                / group_path
                / f"{string_to_snake_case(parts[-1])}.py"
            )
            if not cmd_path.exists():
                continue

            request = CommandRequest(
                kernel=self.kernel,
                name=f"@{service.name}::{hook}",
                arguments={"app_path": str(app_workdir.get_path()), **(arguments or {})},
                output_target=[OUTPUT_TARGET_NONE],
            )
            response = self.kernel.execute_kernel_command(request)
            results[service.name] = (
                response.content if hasattr(response, "content") else None
            )

        return results

    def find_service_dir(self, service_name: str) -> Path | None:
        from wexample_wex_core.resolver.service_command_resolver import _SERVICES_SUBDIR

        for addon in self.kernel.get_addons().values():
            service_dir = addon.workdir.get_path() / _SERVICES_SUBDIR / service_name
            if service_dir.is_dir():
                return service_dir
        return None

    def get_service_inheritance_chain(self, service_name: str) -> list[str]:
        chain: list[str] = []
        current = service_name
        visiting: set[str] = set()

        while current:
            if current in visiting:
                raise ValueError(
                    f"Cyclic service inheritance detected: {' -> '.join(chain + [current])}"
                )

            visiting.add(current)
            chain.append(current)
            manifest = self.get_service_manifest_raw(current)
            parent = manifest.get("extends")
            current = str(parent) if parent else ""

        chain.reverse()
        return chain

    def get_service_manifest_raw(self, service_name: str) -> dict[str, Any]:
        from wexample_helpers_yaml.helpers.yaml_helpers import yaml_read

        service_dir = self.find_service_dir(service_name)
        if service_dir is None:
            return {}

        return yaml_read(file_path=str(service_dir / "service.yml"), default={}) or {}

    def get_service_manifest(self, service_name: str) -> dict[str, Any]:
        from wexample_helpers.helpers.dict import dict_merge

        chain = self.get_service_inheritance_chain(service_name)
        merged: dict[str, Any] = {}
        list_keys = {"tags", "dependencies"}

        for inherited_service_name in chain:
            raw_manifest = self.get_service_manifest_raw(inherited_service_name)
            merged = dict_merge(merged, raw_manifest)

            for key in list_keys:
                values: list[Any] = []
                for source in (merged, raw_manifest):
                    for value in source.get(key, []) or []:
                        if value not in values:
                            values.append(value)
                if values:
                    merged[key] = values

        merged.pop("extends", None)
        return merged

    def find_services_by_tag(self, tag: str) -> list[str]:
        from wexample_wex_core.resolver.service_command_resolver import _SERVICES_SUBDIR

        matches: list[str] = []
        for addon in self.kernel.get_addons().values():
            services_dir = addon.workdir.get_path() / _SERVICES_SUBDIR
            if not services_dir.is_dir():
                continue

            for service_dir in sorted(services_dir.iterdir()):
                if not service_dir.is_dir():
                    continue

                manifest = self.get_service_manifest(service_dir.name)
                if tag in (manifest.get("tags") or []):
                    matches.append(service_dir.name)

        return matches

    @staticmethod
    def get_helper_app_path(name: str, env: str) -> Path:
        from wexample_wex_addon_app.helpers.app import get_helper_app_path

        return get_helper_app_path(name=name, env=env)

    def get_command_resolver_classes(self) -> list[type[AbstractCommandResolver]]:
        from wexample_wex_addon_app.resolver.app_command_resolver import AppCommandResolver
        from wexample_wex_addon_app.resolver.service_command_resolver import ServiceCommandResolver

        return [AppCommandResolver, ServiceCommandResolver]

    def get_middlewares_classes(self) -> list[type[AbstractMiddleware]]:
        from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
        from wexample_wex_addon_app.middleware.each_suite_package_middleware import (
            EachSuitePackageMiddleware,
        )
        from wexample_wex_addon_app.middleware.package_suite_middleware import (
            PackageSuiteMiddleware,
        )
        from wexample_wex_addon_app.middleware.suite_or_each_package_middleware import (
            SuiteOrEachPackageMiddleware,
        )

        return [
            AppMiddleware,
            EachSuitePackageMiddleware,
            PackageSuiteMiddleware,
            SuiteOrEachPackageMiddleware,
        ]
