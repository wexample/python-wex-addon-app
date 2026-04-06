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

    def get_services(self, app_workdir: AppWorkdir, kernel=None) -> list:
        from wexample_helpers_yaml.helpers.yaml_helpers import yaml_read

        from wexample_wex_addon_app.resolver.service_command_resolver import ServiceCommandResolver
        from wexample_wex_addon_app.service.app_service import AppService

        service_resolver = next(
            (r for r in kernel.get_resolvers() if isinstance(r, ServiceCommandResolver)),
            None,
        ) if kernel else None
        if not service_resolver:
            return []

        app_config = app_workdir.get_config()
        services_config = app_config.search("service")
        if services_config.is_none():
            return []

        result = []
        for service_name in services_config.to_dict():
            service_dir = service_resolver._find_service_dir(service_name)
            manifest = yaml_read(file_path=str(service_dir / "service.yml"), default={}) if service_dir else {}
            result.append(AppService(name=service_name, app_workdir=app_workdir, service_dir=service_dir, manifest=manifest))

        return result

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
