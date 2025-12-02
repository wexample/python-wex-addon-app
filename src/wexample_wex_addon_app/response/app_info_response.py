from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_app.response.abstract_response import AbstractResponse
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.enums.terminal_color import TerminalColor
from wexample_prompt.responses.abstract_prompt_response import AbstractPromptResponse

from wexample_wex_addon_app.workdir.basic_app_workdir import BasicAppWorkdir

if TYPE_CHECKING:
    from wexample_prompt.responses.echo_prompt_response import EchoPromptResponse


@base_class
class AppInfoResponse(AbstractResponse):
    app_workdir: BasicAppWorkdir = public_field(
        description="The application workdir to display information about"
    )

    @staticmethod
    def _format_yes_no(condition: bool) -> str:
        """Format a boolean condition as colored Yes/No.

        Args:
            condition: True for green Yes, False for red No

        Returns:
            Formatted string with color markup
        """
        return "@color:green{Yes}" if condition else "@color:red{No}"

    def _get_coverage_data(self) -> tuple[int, int, int, TerminalColor]:
        """Extract and calculate coverage data from config.

        Returns:
            Tuple of (total, covered, percent, color)
        """
        coverage_last_report = (
            self.app_workdir.get_config()
            .search("test.coverage.last_report")
            .get_dict_or_default()
        )

        if coverage_last_report:
            total = coverage_last_report.get("total")
            covered = coverage_last_report.get("covered")

            total_int = total.get_int() if total else 0
            covered_int = covered.get_int() if covered else 0

            coverage_ratio = (covered_int / total_int) if total_int else 0.0
            clamped_ratio = min(max(coverage_ratio, 0.0), 1.0)
            coverage_percent = int(round(clamped_ratio * 100))
        else:
            total_int = 100
            covered_int = 0
            coverage_percent = 0

        # Determine color based on coverage percentage
        if coverage_percent >= 80:
            coverage_color = TerminalColor.GREEN
        elif coverage_percent > 0:
            coverage_color = TerminalColor.YELLOW
        else:
            coverage_color = TerminalColor.RED

        return total_int, covered_int, coverage_percent, coverage_color

    def _get_formatted_prompt_response(self) -> AbstractPromptResponse:
        """Build the complete app info response with all sections.

        Returns:
            MultiplePromptResponse containing all info sections
        """
        from wexample_app.const.env import ENV_COLORS
        from wexample_prompt.responses.data.multiple_prompt_response import (
            MultiplePromptResponse,
        )
        from wexample_prompt.responses.data.properties_prompt_response import (
            PropertiesPromptResponse,
        )
        from wexample_prompt.responses.interactive.progress_prompt_response import (
            ProgressPromptResponse,
        )
        from wexample_prompt.responses.titles.separator_prompt_response import (
            SeparatorPromptResponse,
        )

        env = self.app_workdir.get_app_env()
        libraries = self._get_libraries_responses()
        total_int, covered_int, coverage_percent, coverage_color = (
            self._get_coverage_data()
        )

        # Check all conditions for publishability
        has_readme = self.app_workdir.has_readme()
        is_clean_since_version = (
            not self.app_workdir.has_changes_since_last_publication_tag()
        )
        has_tests = self.app_workdir.has_a_test()
        is_clean_since_coverage = not self.app_workdir.has_changes_since_last_coverage()

        # App is publishable only if ALL conditions are met
        is_publishable = all(
            [
                has_readme,
                is_clean_since_version,
                has_tests,
                is_clean_since_coverage,
            ]
        )

        # Build response sections
        responses = [
            # Project information
            PropertiesPromptResponse(
                title="Project Info",
                properties={
                    "Name": f"@color:blue{{{self.app_workdir.get_item_name()}}}",
                    "Version": self.app_workdir.get_project_version(),
                    "Path": f"@path{{{self.app_workdir.get_path()}}}",
                    "Environment": f"@color:{ENV_COLORS[env]}{{{env}}}",
                },
            ),
            # Test coverage progress bar
            ProgressPromptResponse(
                total=total_int,
                current=covered_int,
                label=f"Test coverage ({covered_int}/{total_int})",
                color=coverage_color,
                show_percentage=True,
            ),
        ]

        # Add libraries section if any
        if libraries:
            responses.append(
                SeparatorPromptResponse.create_separator(label="Libraries")
            )
            responses.extend(libraries)

        # Add status sections
        responses.extend(
            [
                PropertiesPromptResponse(
                    title="Files",
                    properties={
                        # "Source files": f"@color:magenta{{{self.app_workdir.count_source_files()}}}",
                        # "Test files": f"@color:magenta{{{self.app_workdir.count_test_files()}}}",
                        "Has README.md": self._format_yes_no(has_readme),
                    },
                ),
                PropertiesPromptResponse(
                    title="Code",
                    properties={
                        "Lines in source": f"@color:magenta{{{self.app_workdir.count_source_code_lines()}}}",
                        "Lines in tests": f"@color:magenta{{{self.app_workdir.count_test_code_lines()}}}",
                    },
                ),
                PropertiesPromptResponse(
                    title="Repository",
                    properties={
                        "Clean since last version": self._format_yes_no(
                            is_clean_since_version
                        ),
                    },
                ),
                PropertiesPromptResponse(
                    title="Testing",
                    properties={
                        "Has tests": self._format_yes_no(has_tests),
                        "Clean since last coverage": self._format_yes_no(
                            is_clean_since_coverage
                        ),
                    },
                ),
                PropertiesPromptResponse(
                    title="Status",
                    properties={
                        "Ready to publish": self._format_yes_no(is_publishable),
                    },
                ),
                SeparatorPromptResponse(character="▄"),
            ]
        )

        return MultiplePromptResponse.create_multiple(responses=responses)

    def _get_libraries_responses(self) -> list[EchoPromptResponse]:
        """Get list of library path responses.

        Returns:
            List of EchoPromptResponse for each local library
        """
        from wexample_prompt.responses.echo_prompt_response import EchoPromptResponse

        libraries = []
        local_libraries = self.app_workdir.get_local_libraries_paths()

        if local_libraries:
            for library_config in local_libraries:
                if library_config.is_str():
                    libraries.append(
                        EchoPromptResponse.create_echo(
                            message=f"@path{{{library_config.get_str()}}}"
                        )
                    )

        return libraries
