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
        # Check if --all-packages flag is set
        all_packages = function_kwargs.get("all_packages", False)
        function_kwargs.pop("all_packages")

        if all_packages:
            print("Youpi")

        # Call parent to create contexts normally
        super().build_execution_contexts(
            command_wrapper=command_wrapper,
            request=request,
            function_kwargs=function_kwargs,
        )

        return []

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
