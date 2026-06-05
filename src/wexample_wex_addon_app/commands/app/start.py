from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_app.response.null_response import NullResponse
from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="rebuild",
    type=bool,
    is_flag=True,
    required=False,
    description="Rebuild all Docker images (no cache) then force docker compose up --build",
)
@option(
    name="user",
    type=str,
    required=False,
    description="Owner of application files",
)
@option(
    name="group",
    type=str,
    required=False,
    description="Group of application files",
)
@option(
    name="env",
    type=str,
    required=False,
    description="App environment",
)
@option(
    name="no_proxy",
    type=bool,
    is_flag=True,
    required=False,
    description="Do not start the reverse proxy",
)
@option(
    name="fast",
    type=bool,
    is_flag=True,
    required=False,
    description="Skip config rewrite, just run docker compose up",
)
@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Start the app",
    tags=[
        DomainTag.APP_LIFECYCLE,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__app__start(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    rebuild: bool = False,
    user: str | None = None,
    group: str | None = None,
    env: str | None = None,
    no_proxy: bool = False,
    fast: bool = False,
) -> AbstractResponse:
    from wexample_app.const.globals import APP_PATH_TMP
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

    app_path = app_workdir.get_path()
    tmp_dir = app_path / APP_PATH_TMP
    compose_file = str(tmp_dir / "docker-compose.runtime.yml")
    docker_env_file = str(tmp_dir / "docker.env")

    def _checkup(previous_value=None):
        from wexample_app.response.queue_collection.queued_collection_stop_response import (
            QueuedCollectionStopResponse,
        )

        from wexample_wex_addon_app.commands.app.started import (
            APP_STARTED_CHECK_MODE_ANY_CONTAINER,
            _check_started,
        )

        current_env = app_workdir.get_env_parameter("APP_ENV", default=None)
        if env is not None:
            if current_env != env:
                app_workdir.set_app_env(env)
        elif current_env is None:
            from wexample_wex_addon_app.commands.env.choose import app__env__choose

            context.io.log("No APP_ENV configured, please choose an environment")
            chosen = context.kernel.run_function(app__env__choose)
            if isinstance(chosen, NullResponse):
                return QueuedCollectionStopResponse(
                    kernel=context.kernel,
                    reason="No environment configured, start aborted",
                )

        # Check app-level vars declared in config.yml → vars:
        from wexample_wex_addon_app.helpers.app_vars import check_app_vars_requirements
        from wexample_wex_addon_app.helpers.vars_declaration import (
            process_vars_declarations,
        )

        check_app_vars_requirements(app_workdir=app_workdir, io=context.io)

        # Check vars declared by each installed service (in case the service
        # was added to config.yml without re-running service/install)
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        app_addon_manager = AppAddonManager.from_kernel(context.kernel)
        for service in app_addon_manager.get_app_services(app_workdir):
            process_vars_declarations(
                vars_decl=service.get_vars(),
                app_workdir=app_workdir,
                io=context.io,
            )

        if _check_started(app_workdir, APP_STARTED_CHECK_MODE_ANY_CONTAINER, context):
            return QueuedCollectionStopResponse(
                kernel=context.kernel,
                reason="App is already running",
            )

        return True

    def _proxy(previous_value=None):
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager
        from wexample_wex_addon_app.commands.app.started import (
            APP_STARTED_CHECK_MODE_ANY_CONTAINER,
            _check_started,
        )
        from wexample_wex_addon_app.const.app import SIDECAR_PROXY_NAME

        env = app_workdir.get_app_env()
        proxy_path = AppAddonManager.get_sidecar_path(name=SIDECAR_PROXY_NAME, env=env)

        # Skip if this app IS the proxy
        if app_workdir.get_path().resolve() == proxy_path.resolve():
            return

        # Skip if proxy not required (no sidecar.proxy in config)
        if app_workdir.get_config().search("sidecar.proxy").is_none():
            return

        if no_proxy:
            context.io.log("Proxy explicitly disabled")
            return

        if not proxy_path.exists():
            from wexample_wex_addon_app.commands.sidecar.start import (
                app__sidecar__start,
            )

            return context.kernel.run_function(
                app__sidecar__start,
                {"name": SIDECAR_PROXY_NAME, "env": env},
            )

        proxy_workdir = AppAddonManager.from_kernel(context.kernel).create_app_workdir(
            path=proxy_path
        )
        if proxy_workdir and _check_started(
            proxy_workdir, APP_STARTED_CHECK_MODE_ANY_CONTAINER, context
        ):
            return

        return context.kernel.run_function(
            app__app__start, {"app_path": str(proxy_path)}
        )

    def _config(previous_value=None) -> AbstractResponse:
        from wexample_wex_addon_app.commands.app.perms import app__app__perms
        from wexample_wex_addon_app.commands.config.build import app__config__build

        app_path_str = str(app_path)
        context.kernel.run_function(app__app__perms, {"app_path": app_path_str})
        return context.kernel.run_function(
            app__config__build, {"app_path": app_path_str}
        )

    def _setup_services(previous_value=None) -> None:
        from wexample_wex_addon_app.commands.app.setup import app__app__setup

        context.kernel.run_function(app__app__setup, {"app_path": str(app_path)})

    def _starting(previous_value=None) -> InteractiveShellCommandResponse:
        from wexample_app.response.interactive_shell_command_response import (
            InteractiveShellCommandResponse,
        )

        compose_options = ["up", "-d"]
        if rebuild:
            compose_options.append("--build")

        return InteractiveShellCommandResponse(
            kernel=context.kernel,
            content=[
                "docker",
                "compose",
                "--env-file",
                docker_env_file,
                "-f",
                compose_file,
            ]
            + compose_options,
        )

    def _update_hosts(previous_value=None) -> None:
        import json as _json

        from wexample_wex_addon_app.commands.host.update import app__host__update
        from wexample_wex_addon_app.common.app_registry import registry_register_app

        runtime_path = app_workdir.get_runtime_config_file().get_path()
        if runtime_path.exists():
            with open(runtime_path) as f:
                _data = _json.load(f) or {}
            _data.setdefault("app", {})["started"] = True
            with open(runtime_path, "w") as f:
                _json.dump(_data, f)

        registry_register_app(app_workdir)
        context.kernel.run_function(app__host__update, {"app_path": str(app_path)})

    def _rectify_perms(previous_value=None) -> None:
        from wexample_wex_addon_app.commands.app.perms import app__app__perms

        context.kernel.run_function(app__app__perms, {"app_path": str(app_path)})

    def _pending(previous_value=None) -> None:
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        app_manager = AppAddonManager.from_kernel(context.kernel)

        def _check() -> tuple[bool, list[str]]:
            results = app_manager.run_service_hook(
                hook="service/ready",
                app_workdir=app_workdir,
            )
            all_ready = True
            status_lines = []
            for service_name, ready in results.items():
                if not ready:
                    status_lines.append(f"{service_name} is not ready yet...")
                    all_ready = False
            return all_ready, status_lines

        context.io.pending(
            callback=_check,
            label="Waiting for services...",
            interval=2.0,
        )

    def _complete(previous_value=None) -> AbstractResponse:
        from wexample_app.response.suggestions_response import SuggestionsResponse
        from wexample_wex_core.resolver.addon_command_resolver import (
            AddonCommandResolver,
        )

        from wexample_wex_addon_app.commands.app.go import app__app__go
        from wexample_wex_addon_app.commands.app.stop import app__app__stop
        from wexample_wex_addon_app.commands.db.go import app__db__go

        runtime = app_workdir.get_runtime_config()
        name = runtime.search("app.name").get_str_or_none() or "app"
        env = runtime.search("app.env").get_str_or_default("local")

        domains_config = runtime.search("app.domains")
        domain_lines = []
        if not domains_config.is_none():
            for domain in domains_config.get_list_or_default():
                scheme = "https" if env != "local" else "http"
                domain_lines.append(f"{scheme}://{domain.get_str()}")

        summary = f'App "{name}" started in {env} environment'
        if domain_lines:
            summary += "\n" + "\n".join(domain_lines)

        def _cmd(fn) -> str:
            return AddonCommandResolver.build_command_from_function(fn)

        suggestions = [_cmd(app__app__go), _cmd(app__app__stop)]
        if app_workdir.get_main_db_service():
            suggestions.insert(0, _cmd(app__db__go))

        return SuggestionsResponse(
            kernel=context.kernel,
            message=summary,
            suggestions=suggestions,
        )

    def _rebuild(previous_value=None):
        from wexample_wex_addon_app.commands.image.build import app__image__build

        return context.kernel.run_function(app__image__build, arguments={"all": True})

    if fast:
        # Keep _pending: fast is about skipping config/perms/proxy work, not about
        # racing past services that aren't ready yet (rapidité ≠ précipitation).
        steps = [_starting, _pending]
    else:
        steps = [
            _checkup,
            _proxy,
            _config,
            _setup_services,
            _starting,
            _update_hosts,
            _rectify_perms,
            _pending,
            _complete,
        ]

    if rebuild:
        steps.insert(0, _rebuild)

    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
