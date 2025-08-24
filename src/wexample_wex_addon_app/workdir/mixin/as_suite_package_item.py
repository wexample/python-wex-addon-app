from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


class AsSuitePackageItem:
    def find_suite_workdir(self) -> FrameworkPackageSuiteWorkdir | None:
        from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
            FrameworkPackageSuiteWorkdir,
        )

        return self.find_closest(FrameworkPackageSuiteWorkdir)
