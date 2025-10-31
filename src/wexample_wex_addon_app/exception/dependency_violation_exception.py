from __future__ import annotations

from wexample_app.exception.app_runtime_exception import AppRuntimeException


class DependencyViolationException(AppRuntimeException):
    """Exception raised when a package imports code from another package without a declared dependency."""

    error_code: str = "DEPENDENCY_VIOLATION"

    def __init__(
        self,
        package_name: str,
        imported_package: str,
        import_locations: list[str],
        cause: Exception | None = None,
        previous: Exception | None = None,
    ) -> None:
        from wexample_helpers.helpers.cli import cli_make_clickable_path

        imports_details = "\n".join(
            f" - {cli_make_clickable_path(loc)}" for loc in import_locations
        )

        data = {
            "package_name": package_name,
            "imported_package": imported_package,
            "import_count": len(import_locations),
        }

        super().__init__(
            message=(
                f'Dependency violation: package "{package_name}" imports code from "{imported_package}" '
                f"but there is no declared local dependency path. "
                f'Add "{imported_package}" to the \'project.dependencies\' of "{package_name}" in its pyproject.toml, '
                f'or declare an intermediate local package that depends on "{imported_package}".\n\n'
                f"Detected import locations:\n{imports_details}"
            ),
            data=data,
            cause=cause,
            previous=previous,
        )
