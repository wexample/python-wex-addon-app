from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.middleware.abstract_middleware import AbstractMiddleware

if TYPE_CHECKING:
    from wexample_app.command.option import Option
    from wexample_helpers.const.types import Kwargs
    from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper
    from wexample_wex_core.common.command_request import CommandRequest
    from wexample_wex_core.context.execution_context import ExecutionContext


@base_class
class AppMiddleware(AbstractMiddleware):
    def build_execution_contexts(
        self,
        command_wrapper: CommandMethodWrapper,
        request: CommandRequest,
        function_kwargs: Kwargs,
    ) -> list[ExecutionContext]:
        app_path = function_kwargs.get(
            "app_path", str(request.kernel.call_workdir.get_path())
        )

        function_kwargs.pop("app_path", None)
        function_kwargs["app_workdir"] = self._create_app_workdir(
            request=request, app_path=app_path
        )

        return super().build_execution_contexts(
            command_wrapper=command_wrapper,
            request=request,
            function_kwargs=function_kwargs,
        )

    def _create_app_workdir(self, request: CommandRequest, app_path: str):
        """Create and return the app workdir. Can be overridden by subclasses to add validation."""
        return request.get_addon_manager().create_app_workdir(path=app_path)

    def _get_middleware_options(self) -> list[Option]:
        """Get the default file option definition."""
        from wexample_app.command.option import Option

        return [
            Option(
                name="app_path",
                type=str,
                required=False,
                description="Path to the app directory (defaults to current directory)",
            )
        ]
