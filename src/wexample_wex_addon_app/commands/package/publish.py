from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.suite_or_each_package_middleware import (
    SuiteOrEachPackageMiddleware,
)
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=SuiteOrEachPackageMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish package to PyPI. Use --all-packages to publish all packages in suite.",
)
def app__package__publish(
    context: ExecutionContext,
    app_workdir: CodeBaseWorkdir,
) -> None:
    package_name = app_workdir.get_package_name()
    current_tag = app_workdir.get_publication_tag_name()
    last_tag = app_workdir.get_last_publication_tag()

    if last_tag == current_tag:
        context.io.log(f"{package_name} already published as {current_tag}.")
        return

    app_workdir.publish()
    app_workdir.add_publication_tag()
    context.io.success(f"Published {package_name} as {current_tag}.")
