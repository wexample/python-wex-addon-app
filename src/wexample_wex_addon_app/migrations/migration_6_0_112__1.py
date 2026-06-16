from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from wexample_migration.abstract_migration import AbstractMigration

if TYPE_CHECKING:
    from wexample_migration.migration_context import MigrationContext


def _add_release_target_branch(config: dict) -> bool:
    """Copy `git.main_branch` into a new `git.release_target_branch` key when
    the app uses the `branch_merge` publication strategy and the new key is
    not already set. Returns True if the config was modified.

    `git.main_branch` keeps its original meaning (the protected/primary branch,
    used by filestate-git and by CI as `MAIN_BRANCH_NAME`). The new key
    `git.release_target_branch` is the explicit target of release MRs — this
    split lets projects like TPA target `develop` for releases while keeping
    `master` as the main branch.
    """
    git = config.get("git")
    if not isinstance(git, dict):
        return False

    if git.get("publication_strategy") != "branch_merge":
        return False

    if "release_target_branch" in git:
        return False

    main_branch = git.get("main_branch")
    if not isinstance(main_branch, str) or not main_branch.strip():
        return False

    git["release_target_branch"] = main_branch
    return True


class Migration_6_0_112__1(AbstractMigration):
    VERSION = "6.0.112"
    SEQ = 1
    DESCRIPTION = (
        "Make `git.release_target_branch` explicit for apps using the "
        "`branch_merge` publication strategy. Copies the current value of "
        "`git.main_branch` into a new `git.release_target_branch` key so the "
        "two concepts (primary protected branch vs. release MR target) can "
        "diverge — useful e.g. for git-flow projects where releases merge to "
        "`develop` but `master` remains the main branch."
    )

    def apply(self, context: MigrationContext) -> None:
        config_path = context.target_path / ".wex" / "config.yml"
        if not config_path.is_file():
            return

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            return

        if not _add_release_target_branch(config):
            return

        if context.dry_run:
            return

        with open(config_path, "w") as f:
            yaml.safe_dump(config, f, sort_keys=False)

        kernel = context.extras.get("kernel")
        if kernel:
            release_branch = config["git"]["release_target_branch"]
            kernel.io.log(
                f"Added `git.release_target_branch` = `{release_branch}` to {config_path}."
            )

    def rollback(self, context: MigrationContext) -> None:
        # No rollback: we can't tell whether the user had hand-set
        # release_target_branch == main_branch before this migration.
        return
