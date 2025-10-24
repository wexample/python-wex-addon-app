from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig


@base_class
class WithVersionWorkdirMixin(BaseClass):
    def append_version(self, config: DictConfig | None = None) -> DictConfig:
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.option.text_option import TextOption

        config.get("children").append(
            {
                "name": "version.txt",
                "type": DiskItemType.FILE,
                "should_exist": True,
                "content": self._get_version_default_content(),
                TextOption.get_name(): {"end_new_line": True},
            }
        )

        return config

    def _get_version_default_content(self) -> Any:
        from wexample_helpers.const.version import DEFAULT_VERSION_NUMBER
        from wexample_helpers.helpers.string import string_ensure_end_with_new_line

        return string_ensure_end_with_new_line(DEFAULT_VERSION_NUMBER)
