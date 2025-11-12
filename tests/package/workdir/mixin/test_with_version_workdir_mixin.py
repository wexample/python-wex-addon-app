from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_app.workdir.mixin.with_version_workdir_mixin import (
    WithVersionWorkdirMixin,
)
from wexample_filestate.testing.abstract_workdir_mixin_test import (
    AbstractWorkdirMixinTest,
)
from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig


class TestWithVersionWorkdirMixin(AbstractWorkdirMixinTest):
    """Test WithVersionWorkdirMixin functionality."""

    def _apply_mixin_to_config(self, mixin_instance, config: DictConfig) -> DictConfig:
        """Apply the version mixin method to enhance the config."""
        return mixin_instance.append_version(config)

    def _assert_applied(self, tmp_path) -> None:
        # Check that version.txt exists
        version_file = tmp_path / "version.txt"
        assert version_file.exists(), "version.txt should be created by the mixin"

    def _assert_not_applied(self, tmp_path) -> None:
        # Check that version.txt exists
        version_file = tmp_path / "version.txt"
        assert not version_file.exists(), "version.txt should be created by the mixin"

    def _get_apply_count(self) -> int:
        """Version mixin needs 3 applies: 1 for file creation, 1 for content writing, 1 for text processing."""
        return 2

    def _get_expected_files(self) -> list[str]:
        """Return list of files that should be created by the version mixin."""
        return ["version.txt"]

    def _get_mixin_config(self) -> DictConfig:
        """Return the base configuration for the version mixin test."""
        return {"children": []}

    def _get_test_workdir_class(self) -> type:
        """Return the test class that inherits from WithVersionWorkdirMixin."""

        @base_class
        class VersionWorkdir(WithVersionWorkdirMixin, BaseClass):
            """Test class that inherits from WithVersionWorkdirMixin."""

        return VersionWorkdir
