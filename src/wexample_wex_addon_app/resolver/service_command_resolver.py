from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.resolver.service_command_resolver import (
    ServiceCommandResolver as CoreServiceCommandResolver,
)

if TYPE_CHECKING:
    from wexample_helpers.const.types import Kwargs

    from wexample_wex_core.common.command_method_wrapper import CommandMethodWrapper
    from wexample_wex_core.common.command_request import CommandRequest
    from wexample_wex_core.context.execution_context import ExecutionContext
    from wexample_wex_core.middleware.abstract_middleware import AbstractMiddleware


class ServiceCommandResolver(CoreServiceCommandResolver):
    """App-aware service resolver: injects ``app_workdir`` and ``service: AppService``."""

    def build_execution_context(
        self,
        middleware: AbstractMiddleware | None,
        command_wrapper: CommandMethodWrapper,
        request: CommandRequest,
        function_kwargs: Kwargs,
    ) -> ExecutionContext:
        from wexample_helpers.helpers.string import string_to_snake_case

        from wexample_wex_addon_app.service.app_service import AppService

        service_name = string_to_snake_case(request.match.group(1))

        app_path = function_kwargs.pop("app_path", str(request.kernel.call_workdir.get_path()))
        app_addon_manager = self._get_app_addon_manager()
        app_workdir = app_addon_manager.create_app_workdir(path=app_path)

        function_kwargs["app_workdir"] = app_workdir
        function_kwargs["service"] = AppService(name=service_name, app_workdir=app_workdir)

        return super().build_execution_context(
            middleware=middleware,
            command_wrapper=command_wrapper,
            request=request,
            function_kwargs=function_kwargs,
        )

    def _get_app_addon_manager(self):
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        for addon in self.kernel.get_addons().values():
            if isinstance(addon, AppAddonManager):
                return addon

        raise RuntimeError("AppAddonManager not registered — cannot resolve service context")
