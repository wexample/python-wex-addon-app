from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from wexample_app.const.globals import APP_PATH_APP_MANAGER
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from pathlib import Path

    from wexample_app.resolver.abstract_command_resolver import AbstractCommandResolver
    from wexample_cli.middleware.abstract_middleware import AbstractMiddleware
    from wexample_helpers.const.types import PathOrString

    from wexample_wex_addon_app.service.app_service import AppService
    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@base_class
class AppAddonManager(AbstractAddonManager):
    @classmethod
    def from_kernel(cls, kernel) -> AppAddonManager:
        for addon in kernel.get_addons().values():
            if type(addon) is cls:
                return addon
        raise RuntimeError(f"{cls.__name__} not registered in kernel")

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

    @staticmethod
    def get_sidecar_path(name: str, env: str) -> Path:
        from wexample_wex_addon_app.helpers.app import get_sidecar_path

        return get_sidecar_path(name=name, env=env)

    def create_app_workdir(
        self, path: PathOrString | None = None
    ) -> ManagedWorkdir | None:
        from pathlib import Path

        from wexample_helpers.helpers.cli import cli_make_clickable_path
        from wexample_helpers.helpers.module import module_load_class_from_file

        from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

        app_path = (
            Path(path) if path is not None else self.kernel.call_workdir.get_path()
        )

        if not ManagedWorkdir.is_app_workdir_path(path=app_path):
            self.kernel.warning(
                f"Path does not match with an application directory structure: {cli_make_clickable_path(app_path)}"
            )
            return None

        custom_app_workdir_class_path = (
            app_path / APP_PATH_APP_MANAGER / "app_workdir.py"
        )
        if custom_app_workdir_class_path.exists():
            app_workdir_class = module_load_class_from_file(
                file_path=custom_app_workdir_class_path, class_name="AppWorkdir"
            )
        else:
            app_workdir_class = ManagedWorkdir

        workdir = app_workdir_class.create_from_path(
            path=app_path.resolve(),
            parent_io_handler=self.kernel,
            configure=False,
        )

        children = []
        for service in self.get_app_services(workdir):
            contribution = service.get_workdir_contribution(workdir)
            if contribution:
                children.extend(contribution.get("children", []))

        config = app_workdir_class.get_config_from_path(app_path)
        if config:
            extra = config.read_config().search("workdir.children")
            if not extra.is_none():
                children.extend(extra.to_list())

        workdir.configure(config={"children": children})
        return workdir

    def docker_cp(
        self, service: str, local_src: Path | str, container_dest: str
    ) -> None:
        import subprocess

        container = self.get_service_docker_container_name(service)
        if not container:
            raise RuntimeError(f"No Docker container found for service '{service}'")
        subprocess.run(
            ["docker", "cp", str(local_src), f"{container}:{container_dest}"],
            check=True,
        )

    def docker_exec(self, service: str, args: list[str]) -> str:
        from wexample_helpers.helpers.docker import docker_exec as _docker_exec

        container = self.get_service_docker_container_name(service)
        if not container:
            raise RuntimeError(f"No Docker container found for service '{service}'")
        return _docker_exec(container_name=container, command=args)

    def find_service_dir(self, service_name: str) -> Path | None:
        from wexample_wex_addon_app.resolver.service_command_resolver import (
            _SERVICES_SUBDIR,
        )

        for addon in self.kernel.get_addons().values():
            service_dir = addon.workdir.get_path() / _SERVICES_SUBDIR / service_name
            if service_dir.is_dir():
                return service_dir
        return None

    def find_services_by_tag(self, tag: str) -> list[str]:
        from wexample_wex_addon_app.resolver.service_command_resolver import (
            _SERVICES_SUBDIR,
        )

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

    def get_app_service(
        self, service_name: str, app_workdir: ManagedWorkdir
    ) -> AppService:
        from wexample_helpers.helpers.module import module_load_class_from_file

        from wexample_wex_addon_app.service.app_service import AppService

        service_dir = self.find_service_dir(service_name)
        manifest = self.get_service_manifest(service_name) if service_dir else {}

        service_class = AppService
        if service_dir:
            custom_class_path = service_dir / "app_service.py"
            if custom_class_path.exists():
                service_class = module_load_class_from_file(
                    file_path=custom_class_path,
                    class_name="AppService",
                )

        return service_class(
            name=service_name,
            app_workdir=app_workdir,
            addon_manager=self,
            service_dir=service_dir,
            manifest=manifest,
        )

    def get_app_services(self, app_workdir: ManagedWorkdir) -> list[AppService]:
        # "default" is always injected first — provides base compose (stdin_open, tty, restart, network)
        result = [self.get_app_service("default", app_workdir)]

        services_config = app_workdir.get_config().search("service")
        if not services_config.is_none():
            result.extend(
                self.get_app_service(service_name, app_workdir)
                for service_name in services_config.to_dict()
            )

        return result

    def get_command_resolver_classes(self) -> list[type[AbstractCommandResolver]]:
        from wexample_wex_addon_app.resolver.app_command_resolver import (
            AppCommandResolver,
        )
        from wexample_wex_addon_app.resolver.service_command_resolver import (
            ServiceCommandResolver,
        )

        return [AppCommandResolver, ServiceCommandResolver]

    def get_local_configurable_keys(self) -> list[dict]:
        from wexample_wex_addon_app.helpers.app import detect_ssh_socket

        return [
            {
                "key": "SSH_AUTH_SOCK",
                "description": "SSH agent socket — required for git push/pull over SSH",
                "detect": detect_ssh_socket,
                "default_candidates": [
                    "/run/user/1000/keyring/ssh",
                    "/run/user/1000/gnupg/S.gpg-agent.ssh",
                ],
            }
        ]

    def get_middlewares_classes(self) -> list[type[AbstractMiddleware]]:
        from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
        from wexample_wex_addon_app.middleware.code_base_middleware import (
            CodeBaseMiddleware,
        )
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
            CodeBaseMiddleware,
            EachSuitePackageMiddleware,
            PackageSuiteMiddleware,
            SuiteOrEachPackageMiddleware,
        ]

    def get_service_docker_container_name(self, service: str) -> str | None:
        app_workdir = self.create_app_workdir()
        if app_workdir is None:
            return None
        return app_workdir.docker_build_long_container_name(service)

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

    def get_service_manifest_raw(self, service_name: str) -> dict[str, Any]:
        from wexample_helpers_yaml.helpers.yaml_helpers import yaml_read

        service_dir = self.find_service_dir(service_name)
        if service_dir is None:
            return {}

        return yaml_read(file_path=str(service_dir / "service.yml"), default={}) or {}

    def get_step_guard_classes(self) -> list[type]:
        from wexample_wex_addon_app.yaml.app_should_run_step_guard import (
            AppShouldRunStepGuard,
        )

        return [AppShouldRunStepGuard]

    def get_webhook_resolvers(self) -> dict:
        from wexample_wex_addon_app.webhook.app_resolver import AppWebhookTypeResolver

        return {"app": AppWebhookTypeResolver()}

    def run_app_command(
        self,
        command: str,
        app_workdir: ManagedWorkdir,
        arguments: dict | None = None,
        silent: bool = False,
    ) -> Any:
        import os

        from wexample_app.exception.command_type_not_found_exception import (
            CommandTypeNotFoundException,
        )
        from wexample_wex_core.common.command_request import CommandRequest

        prev_cwd = os.getcwd()
        try:
            os.chdir(app_workdir.get_path())
            request = CommandRequest(
                kernel=self.kernel,
                name=command,
                arguments={
                    "app_path": str(app_workdir.get_path()),
                    **(arguments or {}),
                },
            )
            response = self.kernel.execute_kernel_command(request)
            return response.content if hasattr(response, "content") else None
        except CommandTypeNotFoundException:
            if not silent:
                raise
            return None
        finally:
            os.chdir(prev_cwd)

    def run_service_hook(
        self,
        hook: str,
        app_workdir: ManagedWorkdir,
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
        parts = hook.split("/")
        group_path = Path(*parts[:-1]) if len(parts) > 1 else Path()
        hook_cmd_filename = f"{string_to_snake_case(parts[-1])}.py"
        for service in self.get_app_services(app_workdir):
            if not service.service_dir:
                continue

            cmd_path = (
                service.service_dir / "commands" / group_path / hook_cmd_filename
            )
            if not cmd_path.exists():
                continue

            request = CommandRequest(
                kernel=self.kernel,
                name=f"@{service.address_name}::{hook}",
                arguments={
                    "app_path": str(app_workdir.get_path()),
                    **(arguments or {}),
                },
                output_target=[OUTPUT_TARGET_NONE],
            )
            response = self.kernel.execute_kernel_command(request)
            results[service.name] = (
                response.content if hasattr(response, "content") else None
            )

        return results
