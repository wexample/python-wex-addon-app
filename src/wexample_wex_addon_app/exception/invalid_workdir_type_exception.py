from __future__ import annotations

from wexample_app.exception.app_runtime_exception import AppRuntimeException


class InvalidWorkdirTypeException(AppRuntimeException):
    """Exception raised when a workdir is not of the expected type."""

    error_code: str = "INVALID_WORKDIR_TYPE"

    def __init__(
        self,
        workdir_path: str,
        actual_type: str,
        expected_type: str,
        suite_path: str | None = None,
        cause: Exception | None = None,
        previous: Exception | None = None,
    ) -> None:
        from wexample_helpers.helpers.cli import cli_make_clickable_path

        clickable_path = cli_make_clickable_path(workdir_path)

        data = {
            "workdir_path": workdir_path,
            "actual_type": actual_type,
            "expected_type": expected_type,
        }

        message = (
            f"The app_workdir {clickable_path} is of type {actual_type} "
            f"and not a subclass of {expected_type}."
        )

        if suite_path:
            clickable_suite_path = cli_make_clickable_path(suite_path)
            message += f"\nSuite workdir found at: {clickable_suite_path}"
            data["suite_path"] = suite_path

        super().__init__(
            message=message,
            data=data,
            cause=cause,
            previous=previous,
        )
