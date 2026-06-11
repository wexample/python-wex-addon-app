from __future__ import annotations

from typing import ClassVar

from wexample_app.exception.app_runtime_exception import AppRuntimeException
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class


@base_class
class GitRemoteException(AppRuntimeException):
    """Exception raised when a git remote operation fails."""

    branch_name: str | None = public_field(
        default=None,
        description="Branch involved in the operation, if any",
    )
    error_code: ClassVar[str] = "GIT_REMOTE_ERROR"
    operation: str = public_field(
        default="push",
        description="Git remote operation that failed",
    )
    package_name: str = public_field(description="Name of the affected package")
    remote_name: str = public_field(
        default="origin",
        description="Name of the git remote",
    )
    workdir_path: str = public_field(description="Path of the git working directory")

    def _build_message(self) -> str:
        from wexample_helpers.helpers.cli import cli_make_clickable_path

        clickable_path = cli_make_clickable_path(self.workdir_path)

        message = (
            f"Git remote operation '{self.operation}' failed for package {self.package_name} at {clickable_path}. "
            f"The remote '{self.remote_name}' does not appear to be configured correctly."
        )

        if self.branch_name:
            message += f"\nBranch: {self.branch_name}"

        message += (
            f"\n\nPossible causes:"
            f"\n  - The remote '{self.remote_name}' is not configured"
            f"\n  - The remote URL is invalid or inaccessible"
            f"\n  - The upstream branch does not exist on the remote"
            f"\n\nTo fix this, you may need to:"
            f"\n  - Configure the remote: git remote add {self.remote_name} <url>"
            f"\n  - Set upstream: git push -u {self.remote_name} <branch>"
        )

        return message
