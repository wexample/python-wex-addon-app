from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_app.response.null_response import NullResponse
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@option(
    name="clear_cache",
    type=bool,
    is_flag=True,
    required=False,
    description="Force rebuild of Docker images",
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
@command(type=COMMAND_TYPE_ADDON, description="Start the app")
def app__app__start(
    context: ExecutionContext,
    app_workdir: AppWorkdir,
    clear_cache: bool = False,
    user: str | None = None,
    group: str | None = None,
    env: str | None = None,
    no_proxy: bool = False,
    fast: bool = False,
) -> AbstractResponse:
    from wexample_app.const.globals import WORKDIR_SETUP_DIR
    from wexample_app.response.queued_collection_response import QueuedCollectionResponse
    from wexample_wex_core.const.globals import CORE_DIR_NAME_TMP

    app_path = app_workdir.get_path()
    tmp_dir = app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP
    compose_file = str(tmp_dir / "docker-compose.runtime.yml")
    docker_env_file = str(tmp_dir / "docker.env")

    def _checkup(previous_value=None):
        from wexample_app.const.globals import WORKDIR_SETUP_DIR
        from wexample_app.response.queue_collection.queued_collection_stop_response import (
            QueuedCollectionStopResponse,
        )
        from wexample_filestate.item.file.env_file import EnvFile

        from wexample_wex_addon_app.commands.app.started import (
            APP_STARTED_CHECK_MODE_ANY_CONTAINER,
            _check_started,
        )

        env_file = app_workdir.get_path() / WORKDIR_SETUP_DIR / EnvFile.EXTENSION_DOT_ENV
        if not env_file.exists():
            from wexample_wex_addon_app.commands.env.choose import app__env__choose

            context.io.log("No .wex/.env file found, please choose an environment")
            chosen = context.kernel.run_function(app__env__choose)
            if isinstance(chosen, NullResponse):
                return QueuedCollectionStopResponse(
                    kernel=context.kernel,
                    reason="No environment configured, start aborted",
                )

        if _check_started(app_workdir, APP_STARTED_CHECK_MODE_ANY_CONTAINER, context):
            return QueuedCollectionStopResponse(
                kernel=context.kernel,
                reason="App is already running",
            )

        return True

    def _proxy(previous_value=None):
        from pathlib import Path

        from wexample_wex_addon_app.commands.app.started import (
            APP_STARTED_CHECK_MODE_ANY_CONTAINER,
            _check_started,
        )

        env = app_workdir.get_app_env()

        # Proxy helper app lives at /var/www/{env}/wex-proxy/
        proxy_path = Path(f"/var/www/{env}/wex-proxy")

        # Skip if this app IS the proxy
        if app_workdir.get_path().resolve() == proxy_path.resolve():
            return

        # Skip if proxy not required (no service.proxy in config)
        if app_workdir.get_config().search("service.proxy").is_none():
            return

        if no_proxy:
            context.io.log("Proxy explicitly disabled")
            return

        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        if not proxy_path.exists():
            from wexample_wex_addon_app.commands.helper.start import app__helper__start

            return context.kernel.run_function(app__helper__start, {"env": env})

        proxy_workdir = AppAddonManager.from_kernel(context.kernel).create_app_workdir(
            path=proxy_path
        )
        if proxy_workdir and _check_started(
            proxy_workdir, APP_STARTED_CHECK_MODE_ANY_CONTAINER, context
        ):
            return

        return context.kernel.run_function(app__app__start, {"app_path": str(proxy_path)})

    def _config(previous_value=None) -> AbstractResponse:
        from wexample_wex_addon_app.commands.app.perms import app__app__perms
        from wexample_wex_addon_app.commands.config.write import app__config__write

        app_path_str = str(app_path)
        context.kernel.run_function(app__app__perms, {"app_path": app_path_str})
        return context.kernel.run_function(app__config__write, {"app_path": app_path_str})

    def _starting(previous_value=None):
        from wexample_app.response.interactive_shell_command_response import InteractiveShellCommandResponse

        compose_options = ["up", "-d"]
        if clear_cache:
            compose_options.append("--build")

        return InteractiveShellCommandResponse(
            kernel=context.kernel,
            content=["docker", "compose", "--env-file", docker_env_file, "-f", compose_file] + compose_options,
        )

    def _update_hosts(previous_value=None):
        import yaml

        from wexample_wex_addon_app.commands.hosts.update import app__hosts__update

        runtime_path = app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / "config.runtime.yml"
        if runtime_path.exists():
            with open(runtime_path) as f:
                data = yaml.safe_load(f) or {}
            data["started"] = True
            with open(runtime_path, "w") as f:
                yaml.dump(data, f)

        context.kernel.run_function(app__hosts__update, {"app_path": str(app_path)})

    def _pending(previous_value=None):
        import time

        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        app_manager = AppAddonManager.from_kernel(context.kernel)

        def _check() -> bool:
            results = app_manager.run_service_hook(
                hook="service/ready",
                app_workdir=app_workdir,
            )
            all_ready = True
            for service_name, ready in results.items():
                if not ready:
                    context.io.log(f"{service_name} is not ready yet...")
                    all_ready = False
            return all_ready

        while not _check():
            context.io.log("Waiting for services...")
            time.sleep(2)

    def _complete(previous_value=None):
        from wexample_wex_addon_app.commands.app.go import app__app__go
        from wexample_wex_addon_app.commands.app.stop import app__app__stop
        from wexample_wex_addon_app.commands.db.go import app__db__go
        from wexample_wex_core.resolver.addon_command_resolver import AddonCommandResolver

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

        context.io.suggestions(
            message=summary,
            suggestions=suggestions,
        )

    if fast:
        steps = [_starting]
    else:
        steps = [
            _checkup,
            _proxy,
            _config,
            _starting,
            _update_hosts,
            _pending,
            _complete,
        ]

    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
