from __future__ import annotations

from wexample_wex_addon_app.publication.strategy.abstract_publication_strategy import (
    AbstractPublicationStrategy,
)


class BranchMergePublicationStrategy(AbstractPublicationStrategy):
    """Branch-then-merge workflow — tag is on a branch commit, CI does not trigger
    automatically on push. Delete and re-push the tag after the branch is merged
    to force GitLab to start a new pipeline."""

    def ensure_tag_triggers_ci(self) -> None:
        from wexample_helpers_git.helpers.git import git_push_tag
        from wexample_helpers.helpers.shell import shell_run

        tag = f"v{self.workdir.get_project_version()}"
        cwd = self.workdir.get_path()
        remote = self.workdir._get_deployment_remote_name() or "origin"

        self.workdir.log(f"Re-pushing tag {tag} to force CI trigger…")

        shell_run(
            ["git", "push", remote, f":refs/tags/{tag}"],
            cwd=cwd,
            inherit_stdio=True,
            check=False,
        )
        git_push_tag(tag, cwd=cwd, remote=remote, inherit_stdio=True)
