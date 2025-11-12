from __future__ import annotations

from wexample_app.exception.app_runtime_exception import AppRuntimeException


class GitRemoteException(AppRuntimeException):
    """Exception raised when a git remote operation fails."""

    error_code: str = "GIT_REMOTE_ERROR"

    def __init__(
        self,
        workdir_path: str,
        package_name: str,
        operation: str = "push",
        remote_name: str = "origin",
        branch_name: str | None = None,
        cause: Exception | None = None,
        previous: Exception | None = None,
    ) -> None:
        from wexample_helpers.helpers.cli import cli_make_clickable_path

        clickable_path = cli_make_clickable_path(workdir_path)

        data = {
            "workdir_path": workdir_path,
            "package_name": package_name,
            "operation": operation,
            "remote_name": remote_name,
        }

        message = (
            f"Git remote operation '{operation}' failed for package {package_name} at {clickable_path}. "
            f"The remote '{remote_name}' does not appear to be configured correctly."
        )

        if branch_name:
            message += f"\nBranch: {branch_name}"
            data["branch_name"] = branch_name

        message += (
            f"\n\nPossible causes:"
            f"\n  - The remote '{remote_name}' is not configured"
            f"\n  - The remote URL is invalid or inaccessible"
            f"\n  - The upstream branch does not exist on the remote"
            f"\n\nTo fix this, you may need to:"
            f"\n  - Configure the remote: git remote add {remote_name} <url>"
            f"\n  - Set upstream: git push -u {remote_name} <branch>"
        )

        super().__init__(
            message=message,
            data=data,
            cause=cause,
            previous=previous,
        )
