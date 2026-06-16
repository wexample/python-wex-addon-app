from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_wex_core.resolver.abstract_command_resolver import AbstractCommandResolver

if TYPE_CHECKING:
    from wexample_wex_core.common.command_address import CommandAddress
    from wexample_wex_core.common.command_request import CommandRequest
    from wexample_wex_core.const.registries import RegistryResolverData

_COMMANDS_SUBDIR = "commands"


class AppCommandResolver(AbstractCommandResolver):
    """Resolves commands local to the current app: ``.group/command``

    Walks up from the current working directory looking for a ``{WORKDIR_SETUP_DIR}/commands/``
    directory, exactly as a user would expect when working inside a project.
    """

    @classmethod
    def address_to_command(cls, address: CommandAddress) -> str:
        from wexample_helpers.helpers.string import string_to_kebab_case
        from wexample_wex_core.const.globals import (
            COMMAND_CHAR_APP,
            COMMAND_SEPARATOR_GROUP,
        )

        return f"{COMMAND_CHAR_APP}{string_to_kebab_case(address.group)}{COMMAND_SEPARATOR_GROUP}{string_to_kebab_case(address.name)}"

    @classmethod
    def get_pattern(cls) -> str:
        from wexample_wex_core.const.globals import COMMAND_PATTERN_APP

        return COMMAND_PATTERN_APP

    @classmethod
    def get_type(cls) -> str:
        from wexample_wex_core.const.globals import COMMAND_TYPE_APP

        return COMMAND_TYPE_APP

    @classmethod
    def is_live(cls) -> bool:
        return True

    def autocomplete_suggest(self, cursor: int, search_split: list[str]) -> str | None:
        from wexample_wex_core.const.globals import COMMAND_CHAR_APP

        base = self.get_base_path()
        if not base:
            return None

        # App commands are cwd-relative — scan filesystem directly, not the registry
        commands_base = base / _COMMANDS_SUBDIR
        app_data = self._scan_commands_dir(commands_base, "app")
        app_cmds = sorted(cmd["command"] for cmd in app_data.values())

        if not app_cmds:
            return None

        first = search_split[0] if search_split else ""

        if cursor == 0:
            if first == "":
                return COMMAND_CHAR_APP
            if first.startswith(COMMAND_CHAR_APP):
                matches = [c for c in app_cmds if c.startswith(first)]
                return " ".join(matches) or None

        return None

    def build_command_function_name(self, request: CommandRequest) -> str | None:
        from wexample_helpers.helpers.string import string_to_snake_case
        from wexample_wex_core.common.command_address import CommandAddress

        address = CommandAddress(
            addon="app",
            group=string_to_snake_case(request.match.group(1)),
            name=string_to_snake_case(request.match.group(2)),
        )
        return address.to_function_name()

    def build_command_path(
        self, request: CommandRequest, extension: str
    ) -> Path | None:
        from wexample_helpers.helpers.string import string_to_snake_case
        from wexample_wex_core.common.command_address import CommandAddress

        base = self.get_base_path()
        if not base:
            return None

        address = CommandAddress(
            addon="app",
            group=string_to_snake_case(request.match.group(1)),
            name=string_to_snake_case(request.match.group(2)),
        )
        return base / _COMMANDS_SUBDIR / address.to_relative_path(extension)

    def build_new_command_target(
        self, command: str, extension: str
    ) -> tuple[Path, dict] | None:
        match = self.build_match(command)
        if not match:
            return None

        base = self.get_base_path()
        if not base:
            return None

        group = match.group(1).replace("-", "_")
        name = match.group(2).replace("-", "_")
        target = base / _COMMANDS_SUBDIR / group / f"{name}.{extension}"
        return target, {"_type": "app", "group": group, "name": name}

    def build_registry_data(self) -> RegistryResolverData:
        base = self.get_base_path()
        if not base:
            return {"app": {}}

        commands_base = base / _COMMANDS_SUBDIR
        return {"app": self._scan_commands_dir(commands_base, "app")}

    def get_base_path(self) -> Path | None:
        """Walk up from cwd to find the nearest wex setup directory."""
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        current = Path(os.getcwd())
        while True:
            candidate = current / WORKDIR_SETUP_DIR
            if candidate.is_dir():
                return candidate
            parent = current.parent
            if parent == current:
                return None
            current = parent

    def get_request_addon_manager(self, request: CommandRequest):
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        return AppAddonManager.from_kernel(request.kernel)

    def supports(self, request: CommandRequest) -> object:
        import sys

        from wexample_helpers.helpers.string import string_to_snake_case

        match = self.build_match(request.name)
        if not match:
            return None

        base = self.get_base_path()
        if not base:
            return None

        group = string_to_snake_case(match.group(1))
        name = string_to_snake_case(match.group(2))
        commands_path = base / _COMMANDS_SUBDIR
        if not any((commands_path / group).glob(f"{name}.*")):
            return None

        # Add app commands dir to sys.path so imports work in app scripts
        commands_path_str = str(commands_path)
        if commands_path.is_dir() and commands_path_str not in sys.path:
            sys.path.append(commands_path_str)

        return match
