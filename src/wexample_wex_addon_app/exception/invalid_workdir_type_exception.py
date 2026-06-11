from __future__ import annotations

from typing import ClassVar

from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

from wexample_app.exception.app_runtime_exception import AppRuntimeException


@base_class
class InvalidWorkdirTypeException(AppRuntimeException):
    """Exception raised when a workdir is not of the expected type."""

    error_code: ClassVar[str] = "INVALID_WORKDIR_TYPE"

    workdir_path: str = public_field(description="Path of the workdir")
    actual_type: str = public_field(description="Actual workdir type")
    expected_type: str = public_field(description="Expected workdir type")
    suite_path: str | None = public_field(
        default=None,
        description="Path of the related suite workdir, if any",
    )

    def _build_message(self) -> str:
        from wexample_helpers.helpers.cli import cli_make_clickable_path

        clickable_path = cli_make_clickable_path(self.workdir_path)

        message = (
            f"The app_workdir {clickable_path} is of type {self.actual_type} "
            f"and not a subclass of {self.expected_type}."
        )

        if self.suite_path:
            clickable_suite_path = cli_make_clickable_path(self.suite_path)
            message += f"\nSuite workdir found at: {clickable_suite_path}"

        return message
