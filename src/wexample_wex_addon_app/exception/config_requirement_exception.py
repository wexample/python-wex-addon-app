from __future__ import annotations

from wexample_app.exception.app_runtime_exception import AppRuntimeException


class ConfigRequirementException(AppRuntimeException):
    """Raised when an app config requirement (declared via @require_app_config) is not met."""

    error_code: str = "CONFIG_REQUIREMENT"

    def __init__(
        self,
        message: str,
        path: str,
        value: str | None = None,
        allowed: list | None = None,
    ) -> None:
        data: dict = {"path": path}
        if value is not None:
            data["value"] = value
        if allowed is not None:
            data["allowed"] = allowed
        super().__init__(message=message, data=data)
