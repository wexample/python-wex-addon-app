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
class EachSuitePackageMiddleware(PackageSuiteMiddleware):
    _fail_if_not_suite_workdir: bool = private_field(
        default=False,
        description="Do not restrict the command to work only on package suite",
    )

    def build_execution_contexts(
        self,
        command_wrapper: CommandMethodWrapper,
        request: CommandRequest,
        function_kwargs: Kwargs,
    ) -> list[ExecutionContext]:
        from wexample_wex_core.context.execution_context import ExecutionContext

        # Check if --all-packages flag is set
        all_packages = function_kwargs.get("all_packages", False)
        function_kwargs.pop("all_packages", None)

        # Call parent to get and validate app_workdir,
        # but don't use generated contexts.
        super().build_execution_contexts(
            command_wrapper=command_wrapper,
            request=request,
            function_kwargs=function_kwargs,
        )

        if all_packages:
            suite_workdir = function_kwargs.get("app_workdir")

            if self._is_package_suite_workdir(workdir=suite_workdir):
                # Custom behavior: replace function with our custom one
                def custom_function(context: ExecutionContext, **kwargs) -> None:
                    suite_workdir.packages_execute_manager(
                        command=request.resolver.build_command_from_function(
                            command_wrapper=command_wrapper
                        ),
                        arguments=request.arguments,
                    )
                    return None

                # Create a single context with the custom function
                context = ExecutionContext(
                    middleware=self,
                    command_wrapper=command_wrapper,
                    request=request,
                    function_kwargs=function_kwargs,
                    function=custom_function,
                )

                return [context]

        # Nothing to execute.
        return []

    def _get_middleware_options(self) -> list[Option]:
        """Add the all_packages option."""
        from wexample_app.command.option import Option

        options = super()._get_middleware_options()
        options.append(
            Option(
                name="all_packages",
                type=bool,
                required=False,
                default=False,
                is_flag=True,
                description="Execute the command on all packages of the suite",
            )
        )
        return options
