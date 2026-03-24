from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from wexample_wex_core.resolver.abstract_command_resolver import AbstractCommandResolver

if TYPE_CHECKING:
    from wexample_wex_core.common.command_request import CommandRequest
    from wexample_wex_core.const.registries import RegistryResolverData

# App wex data lives at {app_root}/.wex
_APP_WEX_DIR_NAME = ".wex"
_COMMANDS_SUBDIR = "commands"


class AppCommandResolver(AbstractCommandResolver):
    """Resolves commands local to the current app: ``.group/command``

    Walks up from the current working directory looking for a ``.wex/commands/``
    directory, exactly as a user would expect when working inside a project.
    """

    @classmethod
    def get_pattern(cls) -> str:
        from wexample_wex_core.const.globals import COMMAND_PATTERN_APP

        return COMMAND_PATTERN_APP

    @classmethod
    def get_type(cls) -> str:
        from wexample_wex_core.const.globals import COMMAND_TYPE_APP

        return COMMAND_TYPE_APP

    def get_base_path(self) -> Path | None:
        """Walk up from cwd to find the nearest ``.wex`` directory."""
        current = Path(os.getcwd())
        while True:
            candidate = current / _APP_WEX_DIR_NAME
            if candidate.is_dir():
                return candidate
            parent = current.parent
            if parent == current:
                return None
            current = parent

    def build_command_function_name(self, request: CommandRequest) -> str | None:
        from wexample_helpers.helpers.string import string_to_snake_case

        from wexample_wex_core.common.command_address import CommandAddress

        address = CommandAddress(
            addon="app",
            group=string_to_snake_case(request.match.group(1)),
            name=string_to_snake_case(request.match.group(2)),
        )
        return address.to_function_name()

    def build_command_path(self, request: CommandRequest, extension: str) -> Path | None:
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

    def supports(self, request: CommandRequest) -> object:
        match = self.build_match(request.name)
        if not match:
            return None

        # Only resolve if we're inside an app directory.
        if not self.get_base_path():
            return None

        return match

    def build_registry_data(self) -> RegistryResolverData:
        import importlib.util

        from wexample_wex_core.common.command_address import CommandAddress
        from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper
        from wexample_wex_core.const.registries import RegistryAddonData, RegistryCommandData

        base = self.get_base_path()
        if not base:
            return {}

        commands_base = base / _COMMANDS_SUBDIR
        addon_data: RegistryAddonData = {}

        if commands_base.is_dir():
            for group_dir in sorted(commands_base.iterdir()):
                if not group_dir.is_dir() or group_dir.name.startswith("_"):
                    continue

                for cmd_file in sorted(group_dir.iterdir()):
                    if cmd_file.suffix != ".py" or cmd_file.name.startswith("_"):
                        continue

                    address = CommandAddress.from_path(
                        path=cmd_file,
                        addon_name="app",
                        commands_base=commands_base,
                    )

                    description: str | None = None
                    aliases: list[str] = []
                    func_name = address.to_function_name()
                    spec = importlib.util.spec_from_file_location(func_name, cmd_file)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)  # type: ignore[union-attr]
                        wrapper = getattr(mod, func_name, None)
                        if isinstance(wrapper, CommandMethodWrapper):
                            description = wrapper.description
                            aliases = list(wrapper.aliases)

                    addon_data[address.to_command_key()] = RegistryCommandData(
                        command=address.to_command(),
                        path=str(cmd_file),
                        test=None,
                        description=description,
                        alias=aliases,
                    )

        return {"app": addon_data}
