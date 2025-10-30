from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON)
def app__info__show(
    context: ExecutionContext,
    app_workdir: BasicAppWorkdir,
):
    from wexample_app.response.dict_response import DictResponse

    env = app_workdir.get_app_env()
    
    data = {
        "Name": app_workdir.get_item_name(),
        "Version": app_workdir.get_project_version(),
        "Path": app_workdir.get_path(),
        "Environment": env,
    }
    
    # Show local libraries if configured
    local_libraries = app_workdir.get_local_libraries_paths()
    if local_libraries:
        data["Libraries"] = [library_config.get_str() for library_config in local_libraries]
    
    return DictResponse(kernel=context.kernel, content=data)
