from __future__ import annotations

from wexample_filestate.result.file_state_result import FileStateResult
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import AppWorkdirMixin
from wexample_wex_core.workdir.workdir import Workdir


@base_class
class BasicAppWorkdir(AppWorkdirMixin, Workdir):
    def apply(self, force: bool = False, **kwargs) -> FileStateResult:
        from wexample_helpers.helpers.repo import repo_has_changed_since, repo_get_state

        registry_file = self.get_registry_file()
        registry = registry_file.read_config()

        last_update_hash = registry.search(
            "file_state.last_update_hash"
        ).get_str_or_none()
        if force or (
            last_update_hash is None
            or repo_has_changed_since(
                previous_state=last_update_hash, cwd=self.get_path()
            )
        ):
            result = super().apply(**kwargs)

            # Save hash
            registry.set_by_path(
                "file_state.last_update_hash", repo_get_state(cwd=self.get_path())
            )
            registry_file.write_config()

            return result

        self.io.log("No change since last pass, skipping.", indentation=1)
        return FileStateResult(state_manager=self)
