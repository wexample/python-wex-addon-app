from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.repo_workdir import RepoWorkdir

STRATEGY_MAIN_PUSH = "main_push"
STRATEGY_BRANCH_MERGE = "branch_merge"


class AbstractPublicationStrategy:
    def __init__(self, workdir: RepoWorkdir) -> None:
        self.workdir = workdir

    @staticmethod
    def from_workdir(workdir: RepoWorkdir) -> AbstractPublicationStrategy:
        strategy_name = (
            workdir.get_config()
            .search("git.publication_strategy")
            .get_str_or_default(STRATEGY_MAIN_PUSH)
        )

        if strategy_name == STRATEGY_BRANCH_MERGE:
            from wexample_wex_addon_app.publication.strategy.branch_merge_publication_strategy import (
                BranchMergePublicationStrategy,
            )

            return BranchMergePublicationStrategy(workdir=workdir)

        from wexample_wex_addon_app.publication.strategy.main_push_publication_strategy import (
            MainPushPublicationStrategy,
        )

        return MainPushPublicationStrategy(workdir=workdir)

    def post_push(self) -> None:
        """Called after branch push — e.g. create a merge request."""

    def push(self) -> None:
        """Push the bumped version to the deployment remote.

        Default behaviour pushes the **current branch** (the freshly-created
        ``version-X.Y.Z``) — appropriate for the ``branch_merge`` strategy
        where that branch will later host a merge request.

        Override in strategies that want a different shape (e.g. ``main_push``
        fast-forwards the main branch locally and pushes main only — the
        version branch stays a local-only staging area).
        """
        self.workdir.push_to_deployment_remote()

    def run_post_publish_pipeline(self) -> None:
        """Full post-publish pipeline: MR creation, CI polling, deployment check."""
        self.post_push()
        self.wait_for_ci()
        self.wait_for_deployment()

    def wait_for_ci(self) -> None:
        """Poll CI pipeline until success or failure."""

    def wait_for_deployment(self) -> None:
        """Poll production deployment until the new version is live."""
