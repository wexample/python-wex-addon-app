from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_wex_core.resolver.abstract_command_resolver import AbstractCommandResolver

if TYPE_CHECKING:
    from wexample_helpers.const.types import Kwargs
    from wexample_wex_core.common.command_address import CommandAddress
    from wexample_cli.common.command_method_wrapper import CommandMethodWrapper
    from wexample_wex_core.common.command_request import CommandRequest
    from wexample_wex_core.const.registries import RegistryResolverData
    from wexample_cli.context.execution_context import ExecutionContext
    from wexample_cli.middleware.abstract_middleware import AbstractMiddleware

_SERVICES_SUBDIR = "services"
_COMMANDS_SUBDIR = "commands"


class ServiceCommandResolver(AbstractCommandResolver):
    """Resolves commands scoped to a named service: ``@service::group/command``."""

    @classmethod
    def address_to_command(cls, address: CommandAddress) -> str:
        from wexample_wex_core.const.globals import COMMAND_CHAR_SERVICE

        return f"{COMMAND_CHAR_SERVICE}{super().address_to_command(address)}"

    @classmethod
    def get_pattern(cls) -> str:
        from wexample_wex_core.const.globals import COMMAND_PATTERN_SERVICE

        return COMMAND_PATTERN_SERVICE

    @classmethod
    def get_type(cls) -> str:
        from wexample_wex_core.const.globals import COMMAND_TYPE_SERVICE

        return COMMAND_TYPE_SERVICE

    def autocomplete_suggest(self, cursor: int, search_split: list[str]) -> str | None:
        from wexample_wex_core.const.globals import (
            COMMAND_CHAR_SERVICE,
            COMMAND_SEPARATOR_ADDON,
        )

        service_cmds = list(
            self.kernel.get_configuration_registry().get_all_commands().keys()
        )
        service_cmds = [c for c in service_cmds if c.startswith(COMMAND_CHAR_SERVICE)]

        if not service_cmds:
            return None

        first = search_split[0] if search_split else ""

        if cursor == 0 and first == "":
            return COMMAND_CHAR_SERVICE

        if not first.startswith(COMMAND_CHAR_SERVICE):
            return None

        # Find where "::" sits in search_split — handles both bash behaviours:
        # "@postgres" as one token  → ["@postgres", "::", "db/"]
        # "@" split from name       → ["@", "postgres", "::", "db/"]
        sep_idx = next(
            (i for i, s in enumerate(search_split) if s == COMMAND_SEPARATOR_ADDON),
            None,
        )

        if sep_idx is None:
            # No "::" yet — user is still typing the service name
            typed = "".join(search_split[: cursor + 1])
            suggestions = sorted(
                {
                    c[: c.index(COMMAND_SEPARATOR_ADDON) + len(COMMAND_SEPARATOR_ADDON)]
                    for c in service_cmds
                    if c.startswith(typed) and COMMAND_SEPARATOR_ADDON in c
                }
            )
            return " ".join(suggestions) or None

        # Reconstruct "@service::" regardless of bash word splitting
        service_prefix = "".join(search_split[: sep_idx + 1])

        if cursor == sep_idx:
            # Cursor is on "::" — bash clears CURRENT to ""; suggest all group/commands
            matches = sorted(
                {
                    c[len(service_prefix) :]
                    for c in service_cmds
                    if c.startswith(service_prefix)
                }
            )
            return " ".join(matches) or None

        if cursor > sep_idx:
            # After "::" — filter group/command by partial
            partial = search_split[cursor] if cursor < len(search_split) else ""
            matches = sorted(
                c[len(service_prefix) :]
                for c in service_cmds
                if c.startswith(service_prefix)
                and c[len(service_prefix) :].startswith(partial)
            )
            return " ".join(matches) or None

        return None

    def build_command_function_name(self, request: CommandRequest) -> str | None:
        from wexample_helpers.helpers.string import string_to_snake_case
        from wexample_wex_core.common.command_address import CommandAddress

        address = CommandAddress(
            addon=string_to_snake_case(request.match.group(1)),
            group=string_to_snake_case(request.match.group(2)),
            name=string_to_snake_case(request.match.group(3)),
        )
        return address.to_function_name()

    def build_command_path(
        self, request: CommandRequest, extension: str
    ) -> Path | None:
        from wexample_helpers.helpers.string import string_to_snake_case
        from wexample_wex_core.common.command_address import CommandAddress

        service_name = string_to_snake_case(request.match.group(1))
        service_dir = self._find_service_dir(service_name)
        if not service_dir:
            return None

        address = CommandAddress(
            addon=service_name,
            group=string_to_snake_case(request.match.group(2)),
            name=string_to_snake_case(request.match.group(3)),
        )
        return service_dir / _COMMANDS_SUBDIR / address.to_relative_path(extension)

    def build_execution_context(
        self,
        middleware: AbstractMiddleware | None,
        command_wrapper: CommandMethodWrapper,
        request: CommandRequest,
        function_kwargs: Kwargs,
    ) -> ExecutionContext:
        from wexample_helpers.helpers.string import string_to_snake_case

        from wexample_wex_addon_app.service.app_service import AppService

        service_name = string_to_snake_case(request.match.group(1))

        arguments_dict = (
            request.arguments if isinstance(request.arguments, dict) else {}
        )
        app_path = (
            function_kwargs.pop("app_path", None)
            or arguments_dict.get("app_path")
            or str(request.kernel.call_workdir.get_path())
        )
        app_addon_manager = self._get_app_addon_manager()
        app_workdir = app_addon_manager.create_app_workdir(path=app_path)

        function_kwargs["service"] = AppService(
            name=service_name, app_workdir=app_workdir, addon_manager=app_addon_manager
        )

        return super().build_execution_context(
            middleware=middleware,
            command_wrapper=command_wrapper,
            request=request,
            function_kwargs=function_kwargs,
        )

    def build_registry_data(self) -> RegistryResolverData:
        registry: RegistryResolverData = {}

        self._get_app_addon_manager()
        for addon in self.kernel.get_addons().values():
            services_base = addon.workdir.get_path() / _SERVICES_SUBDIR
            if not services_base.is_dir():
                continue

            for service_dir in sorted(services_base.iterdir()):
                if not service_dir.is_dir() or service_dir.name.startswith("_"):
                    continue

                service_name = service_dir.name
                commands_base = service_dir / _COMMANDS_SUBDIR
                addon_data = self._scan_commands_dir(commands_base, service_name)

                if service_name not in registry:
                    registry[service_name] = addon_data
                else:
                    registry[service_name].update(addon_data)

        return registry

    def _find_service_dir(self, service_name: str) -> Path | None:
        return self._get_app_addon_manager().find_service_dir(service_name)

    def _get_app_addon_manager(self):
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        return AppAddonManager.from_kernel(self.kernel)
