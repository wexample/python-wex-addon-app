from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)
from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
    FrameworkPackageSuiteWorkdir,
)

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

# Semver-friendly labels for internal upgrade type constants
_BUMP_LABELS: dict[str, str] = {
    "major": "major",
    "intermediate": "minor",
    "minor": "patch",
}


@middleware(middleware=PackageSuiteMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Show the publication status of each package in the suite: whether it needs a bump and what version type.",
)
def app__suite__status(
    context: ExecutionContext,
    app_workdir: FrameworkPackageSuiteWorkdir,
) -> None:
    packages = app_workdir.get_ordered_packages()

    rows = []
    for package in packages:
        has_changes = package.has_changes_since_last_publication_tag()
        if has_changes:
            bump_type = package.classify_version_bump()
            bump_label = _BUMP_LABELS.get(bump_type, bump_type)
            status = "to publish"
        else:
            bump_label = "-"
            status = "up to date"

        rows.append([
            package.get_package_name(),
            package.get_project_version(),
            bump_label,
            status,
        ])

    context.io.table(
        data=rows,
        headers=["Package", "Version", "Bump", "Status"],
    )
