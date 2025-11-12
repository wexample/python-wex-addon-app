from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar

from wexample_app.item.file.iml_file import ImlFile


class PythonAppImlFile(ImlFile):
    """
    IntelliJ IDEA .iml helper tailored for Python apps (src/tests layout, python module type).
    """

    MODULE_TYPE: ClassVar[str] = "PYTHON_MODULE"

    def _default_exclude_folders(self) -> Iterable[dict[str, Any]]:
        return (
            {
                "@url": f"{self.MODULE_DIR_URL}/dist",
            },
        )

    def _default_module_attributes(self) -> dict[str, str]:
        attrs = super()._default_module_attributes()
        attrs.setdefault("@type", self.MODULE_TYPE)
        return attrs

    def _default_order_entries(self) -> Iterable[dict[str, Any]]:
        return ({"@type": "sourceFolder", "@forTests": "false"},)

    def _default_source_folders(self) -> Iterable[dict[str, Any]]:
        return (
            {
                "@url": f"{self.MODULE_DIR_URL}/src",
                "@isTestSource": "false",
            },
            {
                "@url": f"{self.MODULE_DIR_URL}/tests",
                "@isTestSource": "true",
            },
        )
