from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_prompt.enums.terminal_color import TerminalColor
from wexample_wex_addon_app.commands.file_state.rectify import app__file_state__rectify
from wexample_wex_addon_app.commands.package.bump import app__package__bump
from wexample_wex_addon_app.commands.package.commit_and_push import (
    app__package__commit_and_push,
)
from wexample_wex_addon_app.commands.package.publish import app__package__publish
from wexample_wex_addon_app.commands.version.propagate import app__version__propagate
from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@option(name="yes", type=bool, default=False, is_flag=True)
@option(name="force", type=bool, default=False, is_flag=True)
@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish package to PyPI. Use --all-packages to publish all packages in suite.",
)
def app__suite__publish(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
    yes: bool = False,
    force: bool = False,
) -> None:
    app_workdir.packages_validate_internal_dependencies_declarations()
    packages = app_workdir.get_ordered_packages()

    context.io.log("Starting deployment...")
    context.io.indentation_up()
    progress = context.io.progress(
        total=len(packages),
        print_response=False,
        color=TerminalColor.CYAN,
    ).get_handle()

    # Process packages in order leaf -> trunk.
    # Use manager for every command allow to use complete specific environment.
    for package in packages:
        progress.advance(label=f"Publishing {package.get_project_name()}", step=1)

        if package.has_changes_since_last_publication_tag():
            # Reserve 1 unit on main progress bar, subdivided into 5 steps
            sub_progress = package.io.progress(
                total=5,
                color=TerminalColor.YELLOW,
                indentation=1,
                print_response=False,
            ).get_handle()

            sub_progress.advance(step=1, label=f"Bumping {package.get_project_name()}")
            bump_args = []
            if force:
                bump_args.append("--force")
            if yes:
                bump_args.append("--yes")
            package.manager_run_command(command=app__package__bump, arguments=bump_args)

            sub_progress.advance(
                step=1, label=f"Rectifying file state for {package.get_project_name()}"
            )
            rectify_args = ["--loop"]
            if yes:
                rectify_args.append("--yes")
            package.manager_run_command(
                command=app__file_state__rectify, arguments=rectify_args
            )

            sub_progress.advance(
                step=1, label=f"Committing and pushing {package.get_project_name()}"
            )
            package.manager_run_command(command=app__package__commit_and_push)

            sub_progress.advance(
                step=1, label=f"Propagating version for {package.get_project_name()}"
            )
            package.manager_run_command(command=app__version__propagate)

            sub_progress.advance(
                step=1, label=f"Publishing {package.get_project_name()}"
            )
            package.manager_run_command(command=app__package__publish)
        else:
            package.io.log("No change to publish, skipping.")

    progress.finish(label="All packages published successfully")
