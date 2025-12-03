from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.config_value.app_license_config_value import (
    AppLicenseConfigValue,
)
from wexample_wex_addon_app.const.path import APP_PATH_LICENSE

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig


@base_class
class WithLicenseWorkdirMixin(BaseClass):
    def append_license(self, config: DictConfig | None = None) -> DictConfig:
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.option.text_option import TextOption

        config.get("children").append(
            {
                "name": APP_PATH_LICENSE,
                "type": DiskItemType.FILE,
                "should_exist": True,
                "content": self._get_license_content(),
                TextOption.get_name(): {"end_new_line": True},
            }
        )

        return config

    def _get_license_content(self) -> AppLicenseConfigValue:
        return AppLicenseConfigValue(workdir=self)
