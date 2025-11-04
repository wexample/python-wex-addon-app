from __future__ import annotations

from typing import TYPE_CHECKING
from wexample_app.response.abstract_response import AbstractResponse
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.enums.terminal_color import TerminalColor
from wexample_prompt.responses.abstract_prompt_response import AbstractPromptResponse
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    pass


@base_class
class AppInfoResponse(AbstractResponse):
    app_workdir: BasicAppWorkdir = public_field(
        description="The application the information is about"
    )

    def _get_formatted_prompt_response(self) -> AbstractPromptResponse:
        from wexample_prompt.responses.interactive.progress_prompt_response import ProgressPromptResponse
        from wexample_prompt.responses.data.multiple_prompt_response import MultiplePromptResponse
        from wexample_prompt.responses.titles.separator_prompt_response import SeparatorPromptResponse
        from wexample_prompt.responses.echo_prompt_response import EchoPromptResponse
        from wexample_app.const.env import ENV_COLORS
        from wexample_prompt.responses.data.properties_prompt_response import (
            PropertiesPromptResponse,
        )

        env = self.app_workdir.get_app_env()

        libraries = []
        # Show local libraries if configured
        local_libraries = self.app_workdir.get_local_libraries_paths()
        if local_libraries:
            for library_config in local_libraries:
                if library_config.is_str():
                    libraries.append(
                        EchoPromptResponse.create_echo(
                            message=f"@path{{{library_config.get_str()}}}"
                        )
                    )

        config = (
            self.app_workdir.get_config()
            .search("test.coverage.last_report")
            .get_dict_or_default()
        )

        if config:
            total = config.get("total")
            covered = config.get("covered")

            total_int = total.get_int() if total else 0
            covered_int = covered.get_int() if covered else 0

            coverage_ratio = (covered_int / total_int) if total_int else 0.0
            clamped_ratio = min(max(coverage_ratio, 0.0), 1.0)
            coverage_percent = int(round(clamped_ratio * 100))
        else:
            total_int = 100
            covered_int = 0
            coverage_percent = 0

        if coverage_percent >= 80:
            coverage_color = TerminalColor.GREEN
        elif coverage_percent > 0:
            coverage_color = TerminalColor.YELLOW
        else:
            coverage_color = TerminalColor.RED

        return MultiplePromptResponse.create_multiple(
            responses=[
                PropertiesPromptResponse(
                    title="Project info",
                    properties={
                        "name": f"@color:blue{{{self.app_workdir.get_item_name()}}}",
                        "version": self.app_workdir.get_project_version(),
                        "path": f"@path{{{self.app_workdir.get_path()}}}",
                        "environment": f"@color:{ENV_COLORS[env]}{{{env}}}",
                    },
                ),
                ProgressPromptResponse(
                    total=total_int,
                    current=covered_int,
                    label=f"Test coverage ({covered_int}/{total_int})",
                    color=coverage_color,
                    show_percentage=True,
                ),
            ]
            + (
                (
                    [SeparatorPromptResponse.create_separator(label="Libraries")]
                    + libraries
                )
                if len(libraries)
                else []
            )
            + [
                PropertiesPromptResponse(
                    properties={
                        # TODO
                        "Has one test": "@color:red{No}",
                        "Has a README.md": "@color:red{No}",
                        "Has change from last coverage": "@color:red{Yes}",
                        "Has change from last version": "@color:red{Yes}",
                    }
                ),
                SeparatorPromptResponse(character="▄"),
            ]
        )
