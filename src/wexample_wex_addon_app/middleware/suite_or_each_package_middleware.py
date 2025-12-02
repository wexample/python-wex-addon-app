from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.private_field import private_field
from wexample_helpers.decorator.base_class import base_class

from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)

if TYPE_CHECKING:
    from wexample_app.command.option import Option
    from wexample_helpers.const.types import Kwargs
    from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper
    from wexample_wex_core.common.command_request import CommandRequest
    from wexample_wex_core.context.execution_context import ExecutionContext


@base_class
class SuiteOrEachPackageMiddleware(PackageSuiteMiddleware):
    """Middleware that allows executing on:
    - The suite itself (default when app_path points to a suite)
    - All packages (with --all-packages)
    - Only packages, excluding suite (with --all-packages --packages-only)
    - Only suite, excluding packages (with --suite-only)
    """

    _fail_if_not_suite_workdir: bool = private_field(
        default=False, description="Can be called both on suite or package"
    )

    def build_execution_contexts(
        self,
        command_wrapper: CommandMethodWrapper,
        request: CommandRequest,
        function_kwargs: Kwargs,
    ) -> list[ExecutionContext]:
        from wexample_wex_core.context.execution_context import ExecutionContext

        # Get flags
        all_packages = function_kwargs.get("all_packages", False)
        packages_only = function_kwargs.get("packages_only", False)
        suite_only = function_kwargs.get("suite_only", False)

        # Remove flags from kwargs
        function_kwargs.pop("all_packages", None)
        function_kwargs.pop("packages_only", None)
        function_kwargs.pop("suite_only", None)

        # Validate conflicting options
        if packages_only and suite_only:
            raise ValueError(
                "Cannot use both --packages-only and --suite-only at the same time."
            )

        # Call parent to get and validate app_workdir
        # Don't fail if not suite when we're not targeting packages
        original_fail_setting = self._fail_if_not_suite_workdir
        if not all_packages and not packages_only:
            self._fail_if_not_suite_workdir = False

        try:
            super().build_execution_contexts(
                command_wrapper=command_wrapper,
                request=request,
                function_kwargs=function_kwargs,
            )
        finally:
            self._fail_if_not_suite_workdir = original_fail_setting

        app_workdir = function_kwargs.get("app_workdir")
        is_suite = self._is_package_suite_workdir(workdir=app_workdir)

        contexts = []

        # Determine what to execute
        execute_suite = not packages_only and (suite_only or not all_packages)
        execute_packages = all_packages or packages_only

        # Execute on suite if requested
        if execute_suite:
            contexts.append(
                ExecutionContext(
                    middleware=self,
                    command_wrapper=command_wrapper,
                    request=request,
                    function_kwargs=function_kwargs.copy(),
                )
            )

        # Execute on packages if requested and we have a suite
        if execute_packages and is_suite:

            def custom_function(context: ExecutionContext, **kwargs) -> None:
                suite_workdir = kwargs.get("app_workdir")
                suite_workdir.packages_execute_manager(
                    command=request.resolver.build_command_from_function(
                        command_wrapper=command_wrapper
                    ),
                    arguments=request.arguments,
                )
                return None

            # Create a context with the custom function for package iteration
            package_kwargs = function_kwargs.copy()
            contexts.append(
                ExecutionContext(
                    middleware=self,
                    command_wrapper=command_wrapper,
                    request=request,
                    function_kwargs=package_kwargs,
                    function=custom_function,
                )
            )

        return contexts

    def _get_middleware_options(self) -> list[Option]:
        """Add options for controlling suite/package execution."""
        from wexample_app.command.option import Option

        options = super()._get_middleware_options()
        options.extend(
            [
                Option(
                    name="all_packages",
                    type=bool,
                    required=False,
                    default=False,
                    is_flag=True,
                    description="Execute the command on all packages of the suite (in addition to suite itself unless --packages-only is used)",
                ),
                Option(
                    name="packages_only",
                    type=bool,
                    required=False,
                    default=False,
                    is_flag=True,
                    description="Execute only on packages, not on the suite itself (implies --all-packages)",
                ),
                Option(
                    name="suite_only",
                    type=bool,
                    required=False,
                    default=False,
                    is_flag=True,
                    description="Execute only on the suite itself, not on packages",
                ),
            ]
        )
        return options
