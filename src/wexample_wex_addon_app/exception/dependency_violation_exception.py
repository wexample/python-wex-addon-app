from __future__ import annotations

from typing import ClassVar

from attrs import Factory
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

from wexample_app.exception.app_runtime_exception import AppRuntimeException


def _build_dependency_violation_message(self: DependencyViolationException) -> str:
    from wexample_helpers.helpers.cli import cli_make_clickable_path

    imports_details = "\n".join(
        f" - {cli_make_clickable_path(loc)}" for loc in self.import_locations
    )

    return (
        f'Dependency violation: package "{self.package_name}" imports code from "{self.imported_package}" '
        f"but there is no declared local dependency path. "
        f'Add "{self.imported_package}" to the \'project.dependencies\' of "{self.package_name}" in its pyproject.toml, '
        f'or declare an intermediate local package that depends on "{self.imported_package}".\n\n'
        f"Detected import locations:\n{imports_details}"
    )


@base_class
class DependencyViolationException(AppRuntimeException):
    """Exception raised when a package imports code from another package without a declared dependency."""

    error_code: ClassVar[str] = "DEPENDENCY_VIOLATION"

    package_name: str = public_field(description="Package performing the import")
    imported_package: str = public_field(description="Package being imported")
    import_locations: list[str] = public_field(
        description="Locations where the undeclared import occurs"
    )
    message: str = public_field(
        default=Factory(_build_dependency_violation_message, takes_self=True),
        description="Human-readable error message",
    )
