from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.middleware.abstract_middleware import AbstractMiddleware
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_app.command.option import Option
    from wexample_cli.common.command_method_wrapper import CommandMethodWrapper
    from wexample_cli.context.execution_context import ExecutionContext
    from wexample_helpers.const.types import Kwargs
    from wexample_wex_core.common.command_request import CommandRequest


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

        config_requirements = command_wrapper.extra.get("config_requirements", [])
        if config_requirements:
            from wexample_wex_addon_app.decorator.require_app_config import (
                check_config_requirements,
            )

            check_config_requirements(
                requirements=config_requirements,
                app_workdir=function_kwargs["app_workdir"],
                io=request.kernel.io,
                function_kwargs=function_kwargs,
            )

        env_requirements = command_wrapper.extra.get("env_requirements", [])
        if env_requirements:
            from wexample_wex_addon_app.decorator.require_local_env import (
                check_env_requirements,
            )

            check_env_requirements(
                requirements=env_requirements,
                app_workdir=function_kwargs["app_workdir"],
                io=request.kernel.io,
                function_kwargs=function_kwargs,
            )

        return super().build_execution_contexts(
            command_wrapper=command_wrapper,
            request=request,
            function_kwargs=function_kwargs,
        )

    def _create_app_workdir(self, request: CommandRequest, app_path: str):
        """Create and return the app workdir. Can be overridden by subclasses to add validation."""
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        return AppAddonManager.from_kernel(request.kernel).create_app_workdir(
            path=app_path
        )

    def _get_middleware_options(self) -> list[Option]:
        from wexample_app.command.option import Option

        return [
            Option(
                name="app_path",
                type=str,
                required=False,
                description="Path to the app directory (defaults to current directory)",
            )
        ]
