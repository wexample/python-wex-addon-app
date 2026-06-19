from __future__ import annotations

from typing import ClassVar

from wexample_app.exception.app_runtime_exception import AppRuntimeException
from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class


@base_class
class DependencyViolationException(AppRuntimeException):
    """Exception raised when a package imports code from another package without a declared dependency."""

    error_code: ClassVar[str] = "DEPENDENCY_VIOLATION"
    import_locations: list[str] = public_field(
        description="Locations where the undeclared import occurs"
    )
    imported_package: str = public_field(description="Package being imported")
    package_name: str = public_field(description="Package performing the import")

    def _build_message(self) -> str:
        from wexample_helpers.helper.cli import cli_make_clickable_path

        imports_details = "\n".join(
            [f" - {cli_make_clickable_path(loc)}" for loc in self.import_locations]
        )

        return (
            f'Dependency violation: package "{self.package_name}" imports code from "{self.imported_package}" '
            f"but there is no declared local dependency path. "
            f'Add "{self.imported_package}" to the \'project.dependencies\' of "{self.package_name}" in its pyproject.toml, '
            f'or declare an intermediate local package that depends on "{self.imported_package}".\n\n'
            f"Detected import locations:\n{imports_details}"
        )
