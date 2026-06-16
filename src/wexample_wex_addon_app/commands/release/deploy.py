from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.as_sudo import as_sudo
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@as_sudo()
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description=(
        "Deploy a published version of the app on the current host: "
        "pull images, sync repo, enable maintenance, restart, disable maintenance, prune. "
        "Apps and services plug in via service hooks and @attach."
    ),
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.DEPLOY,
        DomainTag.GIT,
        DomainTag.PACKAGE,
        DomainTag.RELEASE,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__release__deploy(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.const.env import ENV_NAME_LOCAL
    from wexample_app.const.globals import APP_PATH_TMP
    from wexample_app.response.interactive_shell_command_response import (
        InteractiveShellCommandResponse,
    )
    from wexample_app.response.queued_collection_response import (
        QueuedCollectionResponse,
    )

    from wexample_wex_addon_app.commands.app.restart import app__app__restart
    from wexample_wex_addon_app.commands.cache.clear import app__cache__clear
    from wexample_wex_addon_app.commands.config.build import app__config__build
    from wexample_wex_addon_app.commands.maintenance.disable import (
        app__maintenance__disable,
    )
    from wexample_wex_addon_app.commands.maintenance.enable import (
        app__maintenance__enable,
    )

    app_path = app_workdir.get_path()
    app_path_str = str(app_path)  # computed once; reused by _git_fetch / _git_reset
    tmp_dir = app_path / APP_PATH_TMP
    compose_file = str(tmp_dir / "docker-compose.runtime.yml")
    docker_env_file = str(tmp_dir / "docker.env")

    # Hoist kernel reference: avoids repeated attribute lookup inside each closure.
    kernel = context.kernel

    # Pre-build invariant content lists so each closure allocates nothing on call.
    _pull_cmd = ["docker", "compose", "--env-file", docker_env_file, "-f", compose_file, "pull"]
    # Repos on dev/prod are owned by www-data by convention; running `git` as root
    # would trip "dubious ownership" and leave new files root-owned. Run as
    # www-data so files written by git stay www-data-owned. We're already inside
    # an @as_sudo() deploy so `sudo -u www-data` works without a password prompt.
    _git_fetch_cmd = ["sudo", "-n", "-u", "www-data", "git", "fetch", "origin", "--prune"]
    _git_reset_cmd = ["sudo", "-n", "-u", "www-data", "git", "reset", "--hard", "@{u}"]
    _prune_cmd = ["docker", "system", "prune", "-a", "-f"]

    def _pull(previous_value=None) -> InteractiveShellCommandResponse:
        return InteractiveShellCommandResponse(
            kernel=kernel,
            content=_pull_cmd,
        )

    def _git_fetch(previous_value=None) -> InteractiveShellCommandResponse:
        return InteractiveShellCommandResponse(
            kernel=kernel,
            content=_git_fetch_cmd,
            workdir=app_path_str,
        )

    def _git_reset(previous_value=None) -> InteractiveShellCommandResponse:
        return InteractiveShellCommandResponse(
            kernel=kernel,
            content=_git_reset_cmd,
            workdir=app_path_str,
        )

    def _maintenance_enable(previous_value=None) -> AbstractResponse:
        return kernel.run_function(app__maintenance__enable, arguments={})

    def _cache_clear(previous_value=None) -> AbstractResponse:
        return kernel.run_function(app__cache__clear, arguments={})

    def _config_build(previous_value=None) -> AbstractResponse:
        return kernel.run_function(app__config__build, arguments={})

    def _restart(previous_value=None) -> AbstractResponse:
        return kernel.run_function(app__app__restart, arguments={"fast": True})

    def _maintenance_disable(previous_value=None) -> AbstractResponse:
        return kernel.run_function(app__maintenance__disable, arguments={})

    def _prune(previous_value=None) -> InteractiveShellCommandResponse | None:
        if app_workdir.get_app_env() == ENV_NAME_LOCAL:
            context.io.log("Local env — skipping docker system prune.")
            return None
        return InteractiveShellCommandResponse(
            kernel=kernel,
            content=_prune_cmd,
        )

    return QueuedCollectionResponse(
        kernel=context.kernel,
        content=[
            _pull,
            _git_fetch,
            _git_reset,
            _maintenance_enable,
            _cache_clear,
            _config_build,
            _restart,
            _maintenance_disable,
            _prune,
        ],
    )
