from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

from wexample_wex_addon_app.const.path import APP_PATH_README

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig
    from wexample_filestate.config_value.readme_content_config_value import (
        ReadmeContentConfigValue,
    )


@base_class
class WithReadmeWorkdirMixin(BaseClass):
    def append_readme(self, config: DictConfig | None = None) -> DictConfig:
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.option.text_option import TextOption

        config.get("children").append(
            {
                "name": APP_PATH_README,
                "type": DiskItemType.FILE,
                "should_exist": True,
                "content": self._get_readme_content(),
                TextOption.get_name(): {"end_new_line": True},
            }
        )

        return config

    def has_readme(self) -> bool:
        readme = self.find_by_name(APP_PATH_README)
        return readme.get_path().exists() if readme else None

    def _get_readme_content(self) -> ReadmeContentConfigValue:
        from wexample_wex_addon_app.config_value.app_readme_config_value import (
            AppReadmeConfigValue,
        )

        return AppReadmeConfigValue(workdir=self)
