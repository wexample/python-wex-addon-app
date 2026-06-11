from __future__ import annotations

from typing import ClassVar

from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

from wexample_app.exception.app_runtime_exception import AppRuntimeException


@base_class
class ConfigRequirementException(AppRuntimeException):
    """Raised when an app config requirement (declared via @require_app_config) is not met."""

    error_code: ClassVar[str] = "CONFIG_REQUIREMENT"

    path: str = public_field(description="Config path of the unmet requirement")
    value: str | None = public_field(
        default=None,
        description="Actual config value, if any",
    )
    allowed: list | None = public_field(
        default=None,
        description="Allowed config values, if any",
    )
