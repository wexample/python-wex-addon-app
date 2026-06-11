from __future__ import annotations

from wexample_wex_addon_app.publication.strategy.abstract_publication_strategy import (
    AbstractPublicationStrategy,
)

_DEFAULT_MAIN_BRANCH = "main"


class MainPushPublicationStrategy(AbstractPublicationStrategy):
    """Push directly to main — tag push always triggers CI immediately.

    The local ``version-X.Y.Z`` branch is used purely as a staging area for
    the bump/rectify pass. Once everything is green locally, main is
    fast-forwarded onto it and only main is pushed to the remote. The
    version branch never reaches the remote — no orphan branches, no MR
    dance.
    """

    def push(self) -> None:
        from wexample_helpers_git.helpers.git import (
            git_current_branch,
            git_run,
            git_switch_branch,
        )

        cwd = self.workdir.get_path()
        version_branch = git_current_branch(cwd=cwd, inherit_stdio=False)
        main_branch = (
            self.workdir.get_config()
            .search("git.main_branch")
            .get_str_or_default(_DEFAULT_MAIN_BRANCH)
        )

        # If we're somehow already on main (e.g. resume after a partial run),
        # there is nothing to fast-forward — just push what's there.
        if version_branch == main_branch:
            self.workdir.push_to_deployment_remote(branch_name=main_branch)
            return

        # Fast-forward main onto the version branch. --ff-only fails loudly
        # if main has diverged (e.g. someone pushed during the bump); that's
        # the correct outcome — we don't want a silent merge commit here.
        git_switch_branch(main_branch, cwd=cwd, inherit_stdio=False)
        git_run(
            ["merge", "--ff-only", version_branch],
            cwd=cwd,
            inherit_stdio=False,
        )

        self.workdir.push_to_deployment_remote(branch_name=main_branch)

        # Drop the local staging branch — it served its purpose and the
        # commits now live on main. Remote never saw it (see prepare_commit
        # which skips ensure_upstream for this strategy), so no remote
        # cleanup is needed.
        git_run(
            ["branch", "-D", version_branch],
            cwd=cwd,
            inherit_stdio=False,
        )

    def prepare_commit(self) -> None:
        # No-op: the version branch is a local-only staging area, so we
        # don't want `ensure_upstream` to publish it as a side effect, and
        # the rebase-against-upstream has nothing to do (we just branched
        # off main).
        pass
