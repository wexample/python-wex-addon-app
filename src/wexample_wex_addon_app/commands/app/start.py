from __future__ import annotations

from typing import TYPE_CHECKING

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
        # v6: todo — vérifier existence .wex/.env, proposer env/choose si absent (bloqué par env/choose + env/set)
        # v6: todo — appeler app::app/started pour détecter si déjà démarrée (bloqué par run_function cross-addon)
        context.io.log("Checking app state...")
        return True

    def _proxy(previous_value=None):
        # v6: todo — démarrer le proxy si require_proxy et non démarré (bloqué par proxy helper + app_is_reverse_proxy)
        context.io.log("Proxy step skipped (not yet migrated)")

    def _config(previous_value=None) -> AbstractResponse:
        from wexample_wex_addon_app.commands.app.perms import app__app__perms
        from wexample_wex_addon_app.commands.config.write import app__config__write
        # v6: todo — appeler hook app/start-pre via services (bloqué par migration services)
        # v6: todo — enregistrer l'app dans les proxy apps si require_proxy
        context.kernel.run_function(app__app__perms)
        return context.kernel.run_function(app__config__write)

    def _starting(previous_value=None):
        # v6: todo — appeler hook app/start-options via services pour injecter des options compose supplémentaires
        from wexample_app.response.interactive_shell_command_response import InteractiveShellCommandResponse

        compose_options = ["up", "-d"]
        if clear_cache:
            compose_options.append("--build")

        return InteractiveShellCommandResponse(
            kernel=context.kernel,
            content=["docker", "compose", "--env-file", docker_env_file, "-f", compose_file] + compose_options,
        )

    def _update_hosts(previous_value=None):
        # v6: todo — appeler hosts/update (bloqué par proxy + sudo)
        # Marquer l'app comme démarrée dans le runtime config
        import yaml
        runtime_path = app_path / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / "config.runtime.yml"
        if runtime_path.exists():
            with open(runtime_path) as f:
                data = yaml.safe_load(f) or {}
            data["started"] = True
            with open(runtime_path, "w") as f:
                yaml.dump(data, f)

    def _pending(previous_value=None):
        import time

        def _check() -> bool:
            services = context.middleware.get_services(app_workdir, kernel=context.kernel)
            results = context.middleware.call_service_hook(
                hook="service/ready",
                services=services,
                kernel=context.kernel,
                app_path=str(app_path),
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

    def _serve(previous_value=None):
        # v6: todo — appeler hook app/start-post + app/serve (bloqué par migration services)
        pass

    def _first_init(previous_value=None):
        # v6: todo — appeler hook app/first-init si lock file absent, créer le lock (bloqué par migration services)
        pass

    def _complete(previous_value=None):
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

        context.io.suggestions(
            message=summary,
            suggestions=[
                "wex app::db/go",
                "wex app::app/exec --command bash",
                "wex app::app/stop",
            ],
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
            _serve,
            _first_init,
            _complete,
        ]

    return QueuedCollectionResponse(kernel=context.kernel, content=steps)
