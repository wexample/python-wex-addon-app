from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_filestate.const.types_state_items import TargetFileOrDirectoryType
from wexample_helpers.classes.abstract_method import abstract_method

from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir

if TYPE_CHECKING:
    pass


class RepoWorkdir(ManagedWorkdir):
    def bump(self, interactive: bool = False, force: bool = False, **kwargs) -> bool:
        """Create a version-x.y.z branch, update the version number in config. Don't commit changes."""
        from wexample_helpers.helpers.version import version_increment
        from wexample_prompt.responses.interactive.confirm_prompt_response import (
            ConfirmPromptResponse,
        )

        has_changes = self.has_changes_since_last_publication_tag()
        if not force and not has_changes:
            self.log(f"Package {self.get_package_name()} has no new content to bump.")
            return False

        current_version = self.get_project_version()
        if "type" not in kwargs:
            kwargs["type"] = self.classify_version_bump()
        new_version = version_increment(version=current_version, **kwargs)
        branch_name = f"version-{new_version}"

        self.info(f"Bumping version to {new_version}", prefix=True)

        def _bump() -> None:
            from wexample_helpers.helpers.shell import shell_run
            from wexample_helpers_git.helpers.git import (
                git_current_branch,
                git_switch_branch,
            )

            if git_current_branch(cwd=self.get_path()) == branch_name:
                self.log(
                    message=f'Already on branch "{branch_name}", resuming',
                    indentation=1,
                )
            else:
                # `git branch -f` creates the branch if it doesn't exist, or resets it to
                # HEAD if it does (e.g. a previous failed bump left a stale branch).
                shell_run(
                    ["git", "branch", "-f", branch_name, "HEAD"],
                    cwd=self.get_path(),
                    inherit_stdio=False,
                )
                git_switch_branch(branch_name, cwd=self.get_path(), inherit_stdio=True)
                self.log(message=f'Switched to branch "{branch_name}"', indentation=1)

            self.write_config_value("global.version", new_version)

            self.log(
                message=f'Bumped from "{current_version}" to "{new_version}"',
                indentation=1,
            )

        if interactive:
            changes_message = (
                " The project contains changes since last publication."
                if has_changes
                else ""
            )

            confirm = self.confirm(
                f"Do you want to create a new version for @color:magenta{{{self.get_project_name()}}} in @path{{{self.get_path()}}}?{changes_message} "
                f'This will create/switch to branch "{branch_name}".',
                choices=ConfirmPromptResponse.MAPPING_PRESET_YES_NO,
                default="yes",
            )

            if confirm.is_ok():
                _bump()
                return True
        else:
            _bump()
            return True
        return False

    def check_publish_prerequisites(self) -> None:
        import os
        import pathlib
        import stat

        # OS-level variable — not stored in .wex/local/env.yml on every workdir,
        # so get_env_parameter() would raise KeyNotFoundError. Use os.environ.get() here.
        sock = os.environ.get("SSH_AUTH_SOCK", "")

        if sock:
            try:
                if stat.S_ISSOCK(os.stat(sock).st_mode):
                    return
            except OSError:
                pass
            self.warning(
                f"SSH_AUTH_SOCK points to missing socket {sock!r}, trying auto-detect..."
            )

        os.getuid()
        candidates = (
            [
                p
                for uid_dir in pathlib.Path("/run/user").iterdir()
                if pathlib.Path("/run/user").exists()
                for p in [
                    str(uid_dir / "keyring" / "ssh"),
                    str(uid_dir / "gnupg" / "S.gpg-agent.ssh"),
                ]
            ]
            if pathlib.Path("/run/user").exists()
            else []
        )

        for path in candidates:
            if pathlib.Path(path).is_socket():
                os.environ["SSH_AUTH_SOCK"] = path
                self._persist_env_value("SSH_AUTH_SOCK", path)
                self.info(
                    f"Auto-detected SSH agent socket at {path!r} — saved to .wex/local/env.yml"
                )
                return

        raise RuntimeError(
            "SSH_AUTH_SOCK is not set and no SSH agent socket could be auto-detected.\n"
            "Fix: run `eval $(ssh-agent) && ssh-add`, then `wex configure/env`"
        )

    def classify_version_bump(self) -> str:
        """Return the version bump type for this package based on changes since last tag.

        Handles the no-previous-tag case (first publication → patch) then delegates
        to _classify_version_bump() for language-specific logic.
        """
        from wexample_helpers.const.types import UPGRADE_TYPE_MINOR

        last_tag = self.get_last_publication_tag()
        if last_tag is None:
            # First publication — no previous consumers, nothing to break
            return UPGRADE_TYPE_MINOR

        return self._classify_version_bump(last_tag)

    def count_source_code_lines(self) -> int:
        return self._count_code_lines(self._get_source_code_directories())

    def count_source_files(self) -> int:
        return self._count_files(self._get_source_code_directories())

    def count_test_code_lines(self) -> int:
        return self._count_code_lines(self._get_test_code_directories())

    def count_test_files(self) -> int:
        return self._count_files(self._get_test_code_directories())

    def get_last_publication_tag(self) -> str | None:
        """Return the last publication tag for this package, or None if none exists."""
        from wexample_helpers_git.helpers.git import git_last_tag_for_prefix

        prefix = f"{self.get_package_name()}/v*"
        return git_last_tag_for_prefix(prefix, cwd=self.get_path(), inherit_stdio=False)

    def get_main_code_file_extension(self) -> str | None:
        return None

    def get_package_name(self) -> str:
        return self.get_project_name()

    def get_publication_tag_name(self) -> str:
        """Return the conventional tag name for this package publication.

        Format: "{package_name}/v{version}"
        """
        return f"{self.get_package_name()}/v{self.get_project_version()}"

    def has_a_test(self) -> bool:
        from wexample_wex_addon_app.const.path import APP_PATH_TEST

        test_dir = self.find_by_name(APP_PATH_TEST)
        return (
            test_dir
            and test_dir.is_directory()
            and any(test_dir.get_path().rglob("*.py"))
        )

    def has_changes_since_last_coverage(self) -> bool:
        from wexample_helpers_git.helpers.git import (
            git_has_changes_since_tag,
            git_has_uncommitted_changes,
        )

        last_commit = (
            self.get_config()
            .search("test.coverage.last_report.commit_hash")
            .get_str_or_default()
        )

        if not last_commit:
            return True

        return git_has_uncommitted_changes(
            cwd=self.get_path()
        ) or git_has_changes_since_tag(last_commit, ".", cwd=self.get_path())

    def has_changes_since_last_publication_tag(self) -> bool:
        """Return True if there are any changes (code or deps) since the last publication tag.

        Compares the working tree against the last pub tag so that dep-version
        bumps written by a sibling's propagate_version step are detected even
        before they are committed.  Returns True on first publication (no tag).
        """
        from wexample_helpers_git.helpers.git import git_has_changes_since_tag

        last_tag = self.get_last_publication_tag()
        if last_tag is None:
            return True
        return git_has_changes_since_tag(last_tag, ".", cwd=self.get_path())

    def _do_publish(self, force: bool = False) -> None:
        from wexample_wex_addon_app.publication.strategy.abstract_publication_strategy import (
            AbstractPublicationStrategy,
        )

        if not self.should_be_published(force=force):
            return

        self.check_publish_prerequisites()
        self.clear_runtime_config_cache()
        self._publish(force=force)
        AbstractPublicationStrategy.from_workdir(self).run_post_publish_pipeline()
        self._wait_for_registry()
        self.success(
            f"Published {self.get_package_name()} as {self.get_publication_tag_name()}."
        )
        self.add_publication_tag()
        self._post_publish()

    def publish_dependencies(self) -> dict[str, str]:
        return {self.get_package_name(): self.get_project_version()}

    def release(
        self,
        force: bool = False,
        interactive: bool = True,
        has_changes: bool | None = None,
    ) -> None:
        from wexample_prompt.enums.terminal_color import TerminalColor

        from wexample_wex_addon_app.commands.library.sync import app__library__sync
        from wexample_wex_addon_app.commands.state.rectify import (
            app__state__rectify,
        )
        from wexample_wex_addon_app.commands.version.bump import app__version__bump
        from wexample_wex_addon_app.commands.version.propagate import (
            app__version__propagate,
        )
        from wexample_wex_addon_app.commands.version.push import app__version__push

        # Live check includes uncommitted working-tree changes, so dep-version bumps
        # written by a sibling's propagate_version step during this suite run are
        # detected before they are committed.  Pass has_changes=True/False to
        # override (e.g. --force) or leave None for the default live check.
        _has_changes = (
            has_changes
            if has_changes is not None
            else self.has_changes_since_last_publication_tag()
        )

        # Rectify runs only when there are actual changes (or force=True).
        # This is intentional: rectify itself may generate files (version.txt, README...),
        # but we consider those a consequence of real changes, not a trigger.
        # Use --force to publish even without detected changes (e.g. to force a rectify pass).
        if force or _has_changes:
            sub_progress = self.progress(
                total=7, color=TerminalColor.YELLOW, indentation=1, print_response=False
            ).get_handle()
            sub_progress.advance(
                step=1, label=f"Syncing libraries for {self.get_project_name()}"
            )
            self.manager_run_command(command=app__library__sync)
            sub_progress.advance(step=1, label=f"Bumping {self.get_project_name()}")
            bump_args = []
            if force:
                bump_args.append("--force")
            if not interactive:
                bump_args.append("--yes")
            bump_response = self.manager_run_command(
                command=app__version__bump, arguments=bump_args
            ).get_output_value()
            if not bump_response.is_true():
                return
            sub_progress.advance(
                step=1, label=f"Rectifying file state for {self.get_project_name()}"
            )
            rectify_args = ["--loop", "--changed-only"]
            if not interactive:
                rectify_args.append("--yes")
            self.manager_run_command(
                command=app__state__rectify, arguments=rectify_args
            )
            sub_progress.advance(
                step=1, label=f"Committing and pushing {self.get_project_name()}"
            )
            self.manager_run_command(command=app__version__push)
            sub_progress.advance(
                step=1, label=f"Propagating version for {self.get_project_name()}"
            )
            self.manager_run_command(command=app__version__propagate)
            sub_progress.advance(step=1, label=f"Building {self.get_project_name()}")
            self._run_build_if_present()
            sub_progress.advance(step=1, label=f"Publishing {self.get_project_name()}")
            self._do_publish(force=force)

    def should_be_published(self, force: bool = False) -> bool:
        current_tag = self.get_publication_tag_name()
        last_tag = self.get_last_publication_tag()
        if not force and last_tag == current_tag:
            self.log(f"{self.get_package_name()} already published as {current_tag}.")
            return False
        return True

    def update_dependencies(self, dependencies_map: dict[str, str]) -> None:
        pass

    def _classify_version_bump(self, last_tag: str) -> str:
        """Classify the version bump type given a known previous tag.

        Any change inside a critical directory is treated as major
        (conservative). Falls back to minor (patch) otherwise.
        Override in language-specific workdirs for finer-grained detection.
        """
        from wexample_helpers.const.types import UPGRADE_TYPE_MAJOR, UPGRADE_TYPE_MINOR
        from wexample_helpers_git.helpers.git import git_has_changes_since_tag

        for directory in self._get_critical_directories():
            dir_path = self.get_path() / directory
            if dir_path.exists() and git_has_changes_since_tag(
                last_tag, directory, cwd=self.get_path()
            ):
                return UPGRADE_TYPE_MAJOR

        return UPGRADE_TYPE_MINOR

    def _count_code_lines(self, directories: list[TargetFileOrDirectoryType]) -> int:
        from wexample_file.helper.line import line_count_recursive

        count = 0
        for directory in directories:
            path = (
                directory.get_path()
                if hasattr(directory, "get_path")
                else self.get_path() / directory
            )
            if path.exists():
                count += line_count_recursive(path)
        return count

    def _count_files(self, directories: list[TargetFileOrDirectoryType]) -> int:
        count = 0
        for directory in directories:
            path = (
                directory.get_path()
                if hasattr(directory, "get_path")
                else self.get_path() / directory
            )
            if path.exists():
                count += len(list(path.rglob("*")))
        return count

    @abstract_method
    def _get_critical_directories(self) -> list[str]:
        pass

    def _get_source_code_directories(self) -> list[TargetFileOrDirectoryType]:
        return []

    def _get_test_code_directories(self) -> list[TargetFileOrDirectoryType]:
        return []

    def _persist_env_value(self, key: str, value: str) -> None:
        try:
            from wexample_wex_core.workdir.kernel_workdir import KernelWorkdir

            kernel_workdir = self.parent_io_handler.workdir
            if isinstance(kernel_workdir, KernelWorkdir):
                data = kernel_workdir.get_local_data("env")
                data[key] = value
                kernel_workdir.set_local_data("env", data)
        except Exception:
            pass

    def _post_publish(self) -> None:
        pass

    def _run_build_if_present(self) -> None:
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        AppAddonManager.from_kernel(self.parent_io_handler).run_app_command(
            ".release/build", self, silent=True
        )

    def _publish(self, force: bool = False) -> None:
        pass

    def _wait_for_registry(self) -> None:
        """Wait until the just-published package version is available on the registry.

        No-op by default. Override in language-specific workdirs (npm, PyPI, Packagist…)
        to block the pipeline until the registry has propagated the new version.
        This prevents downstream packages from failing when they try to resolve a
        dependency that was published moments ago.
        """
