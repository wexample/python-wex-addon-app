from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.decorator.require_app_config import require_app_config
from wexample_wex_addon_app.decorator.require_local_env import require_local_env
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware
from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


def _resolve_publish_pipy_token_var(app_workdir: ManagedWorkdir) -> str | None:
    """Return 'PIPY_TOKEN' when the workdir publishes to public PyPI, else None.

    Not required when:
    - The workdir isn't a Python package (PHP/JS/Flutter packages).
    - The workdir publishes to a private registry (pdm.repository.url set) —
      publication then goes through a CI pipeline triggered by a git tag,
      no local `pdm publish` call.
    """
    try:
        from wexample_wex_addon_dev_python.workdir.python_package_workdir import (
            PythonPackageWorkdir,
        )
    except ImportError:
        return None

    if not isinstance(app_workdir, PythonPackageWorkdir):
        return None

    repository_url = app_workdir.search_app_or_suite_runtime_config(
        "pdm.repository.url", default=None
    ).get_str_or_none()
    if repository_url:
        return None

    return "PIPY_TOKEN"


def _resolve_publish_remote_token_var(app_workdir: ManagedWorkdir) -> str | None:
    """Return the env var name holding the remote API token, or None if not needed.

    `main_push` strategy needs no remote token (direct push, no API call).
    `branch_merge` needs the token of the detected remote (GitLab/GitHub/...).
    """
    strategy = (
        app_workdir.get_config()
        .search("git.publication_strategy")
        .get_str_or_default("main_push")
    )
    if strategy != "branch_merge":
        return None

    from wexample_filestate_git.remote.mixin.with_git_remote_mixin import (
        WithGitRemoteMixin,
    )
    from wexample_helpers_git.helpers.git import git_get_remote_url

    remote_name = app_workdir._get_deployment_remote_name() or "origin"
    remote_url = git_get_remote_url(remote_name, cwd=app_workdir.get_path())
    remote_type = WithGitRemoteMixin._detect_remote_type(remote_url)
    if remote_type is None:
        return None

    default = f"{remote_type.get_snake_short_class_name().upper()}_API_TOKEN"
    return (
        app_workdir.get_config()
        .search("git.remote_token_env_var")
        .get_str_or_default(default)
    )


@option(name="force", type=bool, default=False, is_flag=True)
@as_sudo()
@require_app_config(
    path="git.publication_strategy",
    type=str,
    values=["main_push", "branch_merge"],
    description="Publication strategy",
    ask_question="Which publication strategy should be used for this app?",
    on_missing="ask",
)
@require_local_env(
    key=_resolve_publish_remote_token_var,
    description="Remote API token used to create/merge the publication MR",
    ask_question="Paste the remote API token (will be stored in .wex/local/env.yml):",
    on_missing="ask",
)
@require_local_env(
    key=_resolve_publish_pipy_token_var,
    description="PyPI publication token",
    ask_question="Paste your PyPI token (will be stored in .wex/local/env.yml):",
    on_missing="ask",
    use_suite_fallback=True,
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Publish a new version of the app.",
)
def app__release__publish(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    force: bool = False,
) -> None:
    app_workdir.release(force=force, interactive=False)
