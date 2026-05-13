from __future__ import annotations

import time
from typing import TYPE_CHECKING

from wexample_wex_addon_app.publication.strategy.abstract_publication_strategy import (
    AbstractPublicationStrategy,
)

if TYPE_CHECKING:
    from wexample_filestate_git.remote.gitlab_remote import GitlabRemote

_DEFAULT_TOKEN_ENV_VAR = "GITLAB_TOKEN"
_DEFAULT_TARGET_BRANCH = "main"
_DEFAULT_CI_POLL_TIMEOUT = 600
_PIPELINE_RETRY_DELAY = 5
_PIPELINE_RETRY_ATTEMPTS = 6
_POST_MERGE_RETRY_ATTEMPTS = 12


class BranchMergePublicationStrategy(AbstractPublicationStrategy):
    """Branch-then-merge workflow.

    post_push  → create MR (idempotent)
    wait_for_ci → poll the MR pipeline until success, then merge
    """

    def __init__(self, workdir) -> None:
        super().__init__(workdir)
        self._gitlab: GitlabRemote | None = None
        self._namespace: str | None = None
        self._repo_name: str | None = None
        self._mr_iid: int | None = None
        self._target_branch: str = _DEFAULT_TARGET_BRANCH
        self._pre_merge_pipeline_id: int | None = None

    def post_push(self) -> None:
        namespace, name = self._get_repo_info()
        version = self.workdir.get_project_version()
        source_branch = f"version-{version}"
        self._target_branch = (
            self.workdir.get_config()
            .search("git.main_branch")
            .get_str_or_default(_DEFAULT_TARGET_BRANCH)
        )
        target_branch = self._target_branch

        self.workdir.log(f"Creating merge request {source_branch} → {target_branch}…")

        gitlab = self._get_gitlab()
        proposal = gitlab.create_merge_proposal(
            namespace=namespace,
            name=name,
            source_branch=source_branch,
            target_branch=target_branch,
            title=f"Release {version}",
        )
        self._mr_iid = gitlab.get_merge_proposal_id(proposal)
        self.workdir.log(
            f"Merge request !{self._mr_iid} ready: {proposal.get('web_url', '')}"
        )

    def wait_for_ci(self) -> None:
        if not self._mr_iid:
            return

        namespace, name = self._get_repo_info()
        gitlab = self._get_gitlab()
        pipeline_id = self._wait_for_mr_pipeline(gitlab, namespace, name)

        timeout = int(
            self.workdir.get_config()
            .search("git.ci_poll_timeout")
            .get_str_or_default(str(_DEFAULT_CI_POLL_TIMEOUT))
        )

        on_tick = self._make_pipeline_tick_handler(pipeline_id, "Pipeline")
        status = gitlab.poll_pipeline(
            namespace, name, pipeline_id, timeout=timeout, on_tick=on_tick
        )

        if status != "success":
            from wexample_app.exception.app_runtime_exception import AppRuntimeException

            pipelines = gitlab.get_merge_proposal_pipelines(
                namespace, name, self._mr_iid
            )
            web_url = next(
                (p.get("web_url", "") for p in pipelines if p.get("id") == pipeline_id),
                "",
            )
            message = f"Pipeline {pipeline_id} ended with status '{status}'."
            if web_url:
                message += f" See: {web_url}"
            raise AppRuntimeException(message=message)

        self.workdir.log(f"Pipeline succeeded. Merging MR !{self._mr_iid}…")
        branch_pipelines = gitlab.get_branch_pipelines(
            namespace, name, self._target_branch
        )
        self._pre_merge_pipeline_id = (
            branch_pipelines[0]["id"] if branch_pipelines else None
        )
        gitlab.merge_merge_proposal(namespace, name, self._mr_iid)
        self.workdir.log(f"MR !{self._mr_iid} merged.")

    def wait_for_deployment(self) -> None:
        namespace, name = self._get_repo_info()
        gitlab = self._get_gitlab()

        self.workdir.log(f"Waiting for post-merge pipeline on '{self._target_branch}'…")
        pipeline_id = self._wait_for_branch_pipeline(gitlab, namespace, name)

        timeout = int(
            self.workdir.get_config()
            .search("git.ci_poll_timeout")
            .get_str_or_default(str(_DEFAULT_CI_POLL_TIMEOUT))
        )

        on_tick = self._make_pipeline_tick_handler(pipeline_id, "Post-merge pipeline")
        status = gitlab.poll_pipeline(
            namespace, name, pipeline_id, timeout=timeout, on_tick=on_tick
        )

        if status != "success":
            from wexample_app.exception.app_runtime_exception import AppRuntimeException

            raise AppRuntimeException(
                message=f"Post-merge pipeline {pipeline_id} ended with status '{status}'."
            )

        self.workdir.success(
            f"Post-merge pipeline succeeded on '{self._target_branch}'."
        )

    def _build_gitlab_remote(self) -> GitlabRemote:
        from wexample_filestate_git.remote.gitlab_remote import GitlabRemote

        config = self.workdir.get_config()
        token_env_var = config.search("git.gitlab_token_env_var").get_str_or_default(
            _DEFAULT_TOKEN_ENV_VAR
        )
        token = self.workdir.get_env_parameter(token_env_var, default=None)
        if not token:
            from wexample_app.exception.app_runtime_exception import AppRuntimeException

            raise AppRuntimeException(
                message=f"GitLab token not found — set env var {token_env_var!r} or add it to .wex/.env"
            )
        gitlab_url = config.search("git.gitlab_url").get_str_or_default(
            "https://gitlab.com"
        )
        remote = GitlabRemote(
            api_token=token,
            base_url=f"{gitlab_url.rstrip('/')}/api/v4",
            io=self.workdir.io,
        )
        remote.setup()
        return remote

    def _get_gitlab(self) -> GitlabRemote:
        if self._gitlab is None:
            self._gitlab = self._build_gitlab_remote()
        return self._gitlab

    def _get_repo_info(self) -> tuple[str, str]:
        if self._namespace and self._repo_name:
            return self._namespace, self._repo_name

        from wexample_helpers.helpers.shell import shell_run

        remote_name = self.workdir._get_deployment_remote_name() or "origin"
        result = shell_run(
            ["git", "remote", "get-url", remote_name],
            cwd=self.workdir.get_path(),
            inherit_stdio=False,
        )
        repo_info = self._get_gitlab().parse_repository_url(
            (result.stdout or "").strip()
        )
        self._namespace = repo_info["namespace"]
        self._repo_name = repo_info["name"]
        return self._namespace, self._repo_name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _make_pipeline_tick_handler(self, pipeline_id: int, label: str):
        """Return an on_tick callback that overwrites its line in place with a colored status dot."""
        _SYMBOL = "⬤"
        _COLOR = {
            "success": "green",
            "failed": "red",
            "canceled": "red",
        }

        state: dict = {"last": None}

        def on_tick(status: str, elapsed: int) -> None:
            color = _COLOR.get(status, "blue")
            if state["last"] is not None:
                self.workdir.io.erase_response(state["last"])
            state["last"] = self.workdir.log(
                f"@color:{color}{{{_SYMBOL}}}  {label} {pipeline_id} — {status} ({elapsed}s)"
            )

        return on_tick

    def _wait_for_branch_pipeline(self, gitlab, namespace: str, name: str) -> int:
        """Wait until a new pipeline appears on the target branch after the merge."""
        baseline = self._pre_merge_pipeline_id
        for _ in range(_POST_MERGE_RETRY_ATTEMPTS):
            pipelines = gitlab.get_branch_pipelines(
                namespace, name, self._target_branch
            )
            if pipelines:
                latest_id = pipelines[0]["id"]
                if baseline is None or latest_id > baseline:
                    return latest_id
            self.workdir.log(
                f"No new pipeline on '{self._target_branch}' yet, retrying in {_PIPELINE_RETRY_DELAY}s…"
            )
            time.sleep(_PIPELINE_RETRY_DELAY)
        from wexample_app.exception.app_runtime_exception import AppRuntimeException

        raise AppRuntimeException(
            message=f"No post-merge pipeline appeared on '{self._target_branch}' after "
            f"{_POST_MERGE_RETRY_ATTEMPTS * _PIPELINE_RETRY_DELAY}s"
        )

    def _wait_for_mr_pipeline(
        self, gitlab: GitlabRemote, namespace: str, name: str
    ) -> int:
        """Wait until the MR has at least one pipeline, then return its ID."""
        for _ in range(_PIPELINE_RETRY_ATTEMPTS):
            pipelines = gitlab.get_merge_proposal_pipelines(
                namespace, name, self._mr_iid
            )
            if pipelines:
                return pipelines[0]["id"]
            self.workdir.log(
                f"No pipeline yet for MR !{self._mr_iid}, retrying in {_PIPELINE_RETRY_DELAY}s…"
            )
            time.sleep(_PIPELINE_RETRY_DELAY)
        from wexample_app.exception.app_runtime_exception import AppRuntimeException

        raise AppRuntimeException(
            message=f"No pipeline found for MR !{self._mr_iid} after "
            f"{_PIPELINE_RETRY_ATTEMPTS * _PIPELINE_RETRY_DELAY}s"
        )
