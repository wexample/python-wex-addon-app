from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.publication.strategy.abstract_publication_strategy import (
    AbstractPublicationStrategy,
)

if TYPE_CHECKING:
    from wexample_filestate_git.remote.abstract_remote import AbstractRemote

_DEFAULT_TARGET_BRANCH = "main"
_DEFAULT_CI_POLL_TIMEOUT = 600
_PIPELINE_RETRY_ATTEMPTS = 360
# Short detection windows for "does this project's CI even run pipelines at
# this stage?". When nothing appears within the budget, we assume the CI is
# configured for the *other* trigger (MR-only or main-push-only) and skip
# the wait rather than burning hours of exponential backoff.
_MR_PIPELINE_DETECT_ATTEMPTS = 6
_POST_MERGE_DETECT_ATTEMPTS = 6


class BranchMergePublicationStrategy(AbstractPublicationStrategy):
    def __init__(self, workdir) -> None:
        super().__init__(workdir)
        self._remote: AbstractRemote | None = None
        self._remote_url: str | None = None
        self._namespace: str | None = None
        self._repo_name: str | None = None
        self._mr_iid: int | None = None
        self._target_branch: str = _DEFAULT_TARGET_BRANCH
        self._pre_merge_pipeline_id: int | None = None

    def post_push(self) -> None:
        namespace, name = self._get_repo_info()
        version = self.workdir.get_setup_version()
        source_branch = f"version-{version}"
        config = self.workdir.get_config()
        # Prefer the explicit publication target; fall back to git.main_branch
        # for projects that haven't split the two concepts yet.
        target = config.search("git.release_target_branch")
        if target.is_none():
            target = config.search("git.main_branch")
        self._target_branch = target.get_str_or_default(_DEFAULT_TARGET_BRANCH)
        target_branch = self._target_branch

        self.workdir.log(f"Creating merge request {source_branch} → {target_branch}…")

        remote = self._get_remote()
        proposal = remote.create_merge_proposal(
            namespace=namespace,
            name=name,
            source_branch=source_branch,
            target_branch=target_branch,
            title=f"Release {version}",
        )
        self._mr_iid = remote.get_merge_proposal_id(proposal)
        self.workdir.log(
            f"Merge request !{self._mr_iid} ready: {proposal.get('web_url', '')}"
        )

    def wait_for_ci(self) -> None:
        if not self._mr_iid:
            return

        namespace, name = self._get_repo_info()
        remote = self._get_remote()
        pipeline_id = self._wait_for_mr_pipeline(remote, namespace, name)

        if pipeline_id is not None:
            timeout = int(
                self.workdir.get_config()
                .search("git.ci_poll_timeout")
                .get_str_or_default(str(_DEFAULT_CI_POLL_TIMEOUT))
            )

            on_tick = self._make_pipeline_tick_handler(pipeline_id, "Pipeline")
            status = remote.poll_pipeline(
                namespace, name, pipeline_id, timeout=timeout, on_tick=on_tick
            )

            if status != "success":
                from wexample_app.exception.app_runtime_exception import (
                    AppRuntimeException,
                )

                pipelines = remote.get_merge_proposal_pipelines(
                    namespace, name, self._mr_iid
                )
                web_url = next(
                    (
                        p.get("web_url", "")
                        for p in pipelines
                        if p.get("id") == pipeline_id
                    ),
                    "",
                )
                message = f"Pipeline {pipeline_id} ended with status '{status}'."
                if web_url:
                    message += f" See: {web_url}"
                raise AppRuntimeException(message=message)

            self.workdir.log(f"Pipeline succeeded. Merging MR !{self._mr_iid}…")
        else:
            self.workdir.log(
                f"No MR pipeline detected for MR !{self._mr_iid} "
                f"(CI likely runs post-merge only). Merging directly…"
            )

        branch_pipelines = remote.get_branch_pipelines(
            namespace, name, self._target_branch
        )
        self._pre_merge_pipeline_id = (
            branch_pipelines[0]["id"] if branch_pipelines else None
        )
        remote.merge_merge_proposal(namespace, name, self._mr_iid)
        self.workdir.log(f"MR !{self._mr_iid} merged.")

    def wait_for_deployment(self) -> None:
        namespace, name = self._get_repo_info()
        remote = self._get_remote()

        self.workdir.log(f"Waiting for post-merge pipeline on '{self._target_branch}'…")
        pipeline_id = self._wait_for_branch_pipeline(remote, namespace, name)

        if pipeline_id is None:
            self.workdir.log(
                f"No post-merge pipeline detected on '{self._target_branch}' "
                f"(CI likely runs MR-only). Skipping post-merge wait."
            )
            return

        timeout = int(
            self.workdir.get_config()
            .search("git.ci_poll_timeout")
            .get_str_or_default(str(_DEFAULT_CI_POLL_TIMEOUT))
        )

        on_tick = self._make_pipeline_tick_handler(pipeline_id, "Post-merge pipeline")
        status = remote.poll_pipeline(
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

    def _build_remote(self) -> AbstractRemote:
        from wexample_filestate_git.remote.mixin.with_git_remote_mixin import (
            WithGitRemoteMixin,
        )

        remote_url = self._get_remote_url()
        remote_type = WithGitRemoteMixin._detect_remote_type(remote_url)
        if remote_type is None:
            from wexample_app.exception.app_runtime_exception import AppRuntimeException

            raise AppRuntimeException(
                message=f"Cannot detect remote type from URL: {remote_url!r}"
            )

        config = self.workdir.get_config()
        default_token_env_var = (
            f"{remote_type.get_snake_short_class_name().upper()}_API_TOKEN"
        )
        token_env_var = config.search("git.remote_token_env_var").get_str_or_default(
            default_token_env_var
        )

        # Token presence is guaranteed by @require_local_env on the publish command,
        # which runs before this method. Defensive assertion in case _build_remote
        # is reached via a different entry point.
        token = self.workdir.get_env_parameter(token_env_var, default=None)
        if not token:
            from wexample_app.exception.app_runtime_exception import AppRuntimeException

            raise AppRuntimeException(
                message=f"Missing required env var: {token_env_var}"
            )

        return remote_type(
            api_token=token,
            base_url=remote_type.build_remote_api_url_from_repo(remote_url),
            io=self.workdir.io,
        )

    def _get_remote(self) -> AbstractRemote:
        if self._remote is None:
            self._remote = self._build_remote()
        return self._remote

    def _get_remote_url(self) -> str:
        if self._remote_url is None:
            from wexample_helpers_git.helpers.git import git_get_remote_url

            remote_name = self.workdir._get_deployment_remote_name() or "origin"
            self._remote_url = git_get_remote_url(
                remote_name, cwd=self.workdir.get_path()
            )
        return self._remote_url

    def _get_repo_info(self) -> tuple[str, str]:
        if self._namespace and self._repo_name:
            return self._namespace, self._repo_name

        remote_url = self._get_remote_url()
        repo_info = self._get_remote().parse_repository_url(remote_url)
        self._namespace = repo_info["namespace"]
        self._repo_name = repo_info["name"]
        return self._namespace, self._repo_name

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _make_pipeline_tick_handler(self, pipeline_id: int, label: str):
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

    def _poll_for_pipeline(
        self,
        check,
        retry_log,
        max_attempts: int,
    ) -> int | None:
        """Poll until `check` returns a pipeline id, or give up at exhaustion.

        Returns the pipeline id on success, or None if no pipeline appeared
        within `max_attempts` — the caller decides what "no pipeline" means
        in its context (MR-only CI vs post-merge-only CI).
        """
        from wexample_helpers.helpers.polling_callback_manager import (
            PollingCallbackManager,
        )

        def on_retry(_attempt, _max, delay, _error, _message) -> None:
            self.workdir.log(retry_log(delay))

        try:
            return PollingCallbackManager(
                callback=check,
                max_attempts=max_attempts,
                on_retry_callback=on_retry,
            ).run()
        except TimeoutError:
            return None

    def _wait_for_branch_pipeline(
        self, remote: AbstractRemote, namespace: str, name: str
    ) -> int | None:
        baseline = self._pre_merge_pipeline_id

        def check() -> int | None:
            pipelines = remote.get_branch_pipelines(
                namespace, name, self._target_branch
            )
            if not pipelines:
                return None
            latest_id = pipelines[0]["id"]
            if baseline is None or latest_id > baseline:
                return latest_id
            return None

        return self._poll_for_pipeline(
            check=check,
            retry_log=lambda delay: (
                f"No new pipeline on '{self._target_branch}' yet, "
                f"retrying in {delay}s…"
            ),
            max_attempts=_POST_MERGE_DETECT_ATTEMPTS,
        )

    def _wait_for_mr_pipeline(
        self, remote: AbstractRemote, namespace: str, name: str
    ) -> int | None:
        def check() -> int | None:
            pipelines = remote.get_merge_proposal_pipelines(
                namespace, name, self._mr_iid
            )
            return pipelines[0]["id"] if pipelines else None

        return self._poll_for_pipeline(
            check=check,
            retry_log=lambda delay: (
                f"No pipeline yet for MR !{self._mr_iid}, "
                f"retrying in {delay}s…"
            ),
            max_attempts=_MR_PIPELINE_DETECT_ATTEMPTS,
        )
