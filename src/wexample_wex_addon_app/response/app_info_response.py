from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_app.const.env import ENV_COLORS
from wexample_app.response.abstract_response import AbstractResponse
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.enums.terminal_color import TerminalColor
from wexample_prompt.responses.abstract_prompt_response import AbstractPromptResponse
from wexample_prompt.responses.data.multiple_prompt_response import MultiplePromptResponse
from wexample_prompt.responses.interactive.progress_prompt_response import ProgressPromptResponse
from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    pass


@base_class
class AppInfoResponse(AbstractResponse):
    app_workdir: BasicAppWorkdir = public_field(
        description="The application the information is about"
    )

    def _get_formatted_prompt_response(self) -> AbstractPromptResponse:
        from wexample_prompt.responses.data.properties_prompt_response import (
            PropertiesPromptResponse,
        )

        env = self.app_workdir.get_app_env()

        data = {}
        # Show local libraries if configured
        local_libraries = self.app_workdir.get_local_libraries_paths()
        if local_libraries:
            for library_config in local_libraries:
                if library_config.is_str():
                    data["libraries"] = library_config.get_str()

        config = self.app_workdir.get_config().search("test.coverage.last_report").get_dict_or_default()

        total = config.get("total")
        covered = config.get("covered")
        return MultiplePromptResponse.create_multiple(
            responses=[
                PropertiesPromptResponse(
                    properties={
                        "name": f"@color:blue{{{self.app_workdir.get_item_name()}}}",
                        "version": self.app_workdir.get_project_version(),
                        "path": str(self.app_workdir.get_path()),
                        "environment": f"@color:{ENV_COLORS[env]}{{{env}}}",
                    },
                ),
                ProgressPromptResponse(
                    total=total.get_int() if total else 0,
                    current=covered.get_int() if covered else 0,
                    label="Test coverage",
                    color=TerminalColor.RED
                )
            ]
        )
