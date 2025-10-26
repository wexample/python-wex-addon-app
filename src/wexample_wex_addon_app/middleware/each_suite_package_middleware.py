from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.middleware.package_suite_middleware import (
    PackageSuiteMiddleware,
)

if TYPE_CHECKING:
    from wexample_helpers.const.types import Kwargs

    from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper
    from wexample_wex_core.common.command_request import CommandRequest
    from wexample_wex_core.context.execution_context import ExecutionContext


@base_class
class EachSuitePackageMiddleware(PackageSuiteMiddleware):
    def build_execution_contexts(
            self,
            command_wrapper: CommandMethodWrapper,
            request: CommandRequest,
            function_kwargs: Kwargs,
    ) -> list[ExecutionContext]:
        from wexample_wex_core.context.execution_context import ExecutionContext

        # Call parent to get and validate app_workdir
        contexts = super().build_execution_contexts(
            command_wrapper=command_wrapper,
            request=request,
            function_kwargs=function_kwargs,
        )

        # Check if --all-packages flag is set
        all_packages = function_kwargs.get("all_packages", False)
        function_kwargs.pop("all_packages", None)

        if not all_packages:
            # Return single context (default behavior)
            return contexts

        # Get the suite workdir from function_kwargs
        suite_workdir = function_kwargs.get("app_workdir")

        # Create one context per package
        package_contexts = []
        for package in suite_workdir.get_packages():
            # Create a copy of kwargs with the package workdir
            package_kwargs = function_kwargs.copy()
            package_kwargs["app_workdir"] = package

            package_contexts.append(
                ExecutionContext(
                    middleware=self,
                    command_wrapper=command_wrapper,
                    request=request,
                    function_kwargs=package_kwargs,
                )
            )

        return package_contexts

    def _get_middleware_options(self) -> list[dict[str, Any]]:
        """Add the all_packages option."""
        options = super()._get_middleware_options()
        options.append({
            "name": "all_packages",
            "type": bool,
            "required": False,
            "default": False,
            "is_flag": True,
            "description": "Execute the command on all packages of the suite",
        })
        return options
