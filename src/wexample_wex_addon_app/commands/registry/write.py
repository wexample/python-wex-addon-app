from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_config.config_value.nested_config_value import NestedConfigValue
from wexample_filestate.item.file.yaml_file import YamlFile
from wexample_wex_core.const.globals import WORKDIR_SETUP_DIR, CORE_DIR_NAME_TMP, CORE_FILE_NAME_REGISTRY

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

from wexample_wex_core.decorator.command import command


@command()
def app__registry__write(
        context: ExecutionContext,
) -> None:
    from wexample_helpers.helpers.cli import cli_make_clickable_path

    workdir = context.request.get_addon_manager().app_workdir()
    registry_path = workdir.get_path() / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / CORE_FILE_NAME_REGISTRY
    registry = YamlFile.create_from_path(
        path=registry_path,
        io=workdir.io
    )

    registry_content = NestedConfigValue(raw={
        'config': workdir.get_config(),
    })

    registry.write_config(registry_content)
    registry.write_parsed()

    context.io.success(
        message=f"Registry updated at: {cli_make_clickable_path(registry_path)}"
    )
