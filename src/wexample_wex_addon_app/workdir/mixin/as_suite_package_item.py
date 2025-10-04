from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
        FrameworkPackageSuiteWorkdir,
    )


@base_class
class AsSuitePackageItem(BaseClass):
    def find_suite_workdir(self) -> FrameworkPackageSuiteWorkdir | None:
        from wexample_wex_addon_app.workdir.framework_packages_suite_workdir import (
            FrameworkPackageSuiteWorkdir,
        )

        return self.find_closest(FrameworkPackageSuiteWorkdir)
