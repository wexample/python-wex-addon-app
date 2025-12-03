from __future__ import annotations

from wexample_filestate.config_value.aggregated_templates_config_value import (
    AggregatedTemplatesConfigValue,
)
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir


@base_class
class AppLicenseConfigValue(AggregatedTemplatesConfigValue):
    workdir: CodeBaseWorkdir = public_field(description="The application workdir")

    def get_templates(self) -> list[str] | None:
        from datetime import datetime

        return [
            "MIT License",
            f"Copyright (c) {datetime.now().year} {self.workdir.get_vendor_name()}",
            "",
            "Permission is hereby granted, free of charge, to any person obtaining a copy",
            'of this software and associated documentation files (the "Software"), to deal',
            "in the Software without restriction, including without limitation the rights",
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell",
            "copies of the Software, and to permit persons to whom the Software is",
            "furnished to do so, subject to the following conditions:",
            "",
            "The above copyright notice and this permission notice shall be included in",
            "all copies or substantial portions of the Software.",
            "",
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR',
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,",
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE",
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER",
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,",
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE",
            "SOFTWARE.",
            "",
        ]
