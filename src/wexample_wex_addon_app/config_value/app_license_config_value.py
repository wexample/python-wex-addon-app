from __future__ import annotations

from wexample_filestate.config_value.aggregated_templates_config_value import AggregatedTemplatesConfigValue
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir


@base_class
class AppLicenseConfigValue(AggregatedTemplatesConfigValue):
    workdir: CodeBaseWorkdir = public_field(description="The application workdir")

    def get_templates(self) -> list[str] | None:
        from datetime import datetime

        return [
            'MIT License',
            f'Copyright (c) {datetime.now().year} {self.workdir.get_vendor_name()}'
        ]
