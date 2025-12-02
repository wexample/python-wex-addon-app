from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_filestate.testing.abstract_workdir_mixin_test import (
    AbstractWorkdirMixinTest,
)
from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

from wexample_wex_addon_app.workdir.mixin.with_readme_workdir_mixin import (
    WithReadmeWorkdirMixin,
)

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig


class TestWithReadmeWorkdirMixin(AbstractWorkdirMixinTest):
    """Test WithReadmeWorkdirMixin functionality."""

    def test_readme_file_created(self, tmp_path) -> None:
        """Test that README.md is created by the mixin."""
        self._setup_with_tmp_path(tmp_path)

        # Create workdir manager with readme mixin
        manager = self._create_test_workdir_manager(tmp_path)

        # Apply once to create the file
        manager.apply()

        # Check that README.md exists
        readme_file = tmp_path / "README.md"
        assert readme_file.exists(), "README.md should be created by the mixin"

    def _apply_mixin_to_config(self, mixin_instance, config: DictConfig) -> DictConfig:
        """Apply the readme mixin method to enhance the config."""
        return mixin_instance.append_readme(config)

    def _assert_applied(self, tmp_path) -> None:
        """Assert that README.md exists."""
        readme_file = tmp_path / "README.md"
        assert readme_file.exists(), "README.md should be created by the mixin"

    def _assert_not_applied(self, tmp_path) -> None:
        """Assert that README.md does not exist."""
        readme_file = tmp_path / "README.md"
        assert not readme_file.exists(), "README.md should not exist"

    def _get_apply_count(self) -> int:
        """Readme mixin needs 2 applies: 1 for file creation, 1 for content writing."""
        return 2

    def _get_expected_files(self) -> list[str]:
        """Return list of files that should be created by the readme mixin."""
        return ["README.md"]

    def _get_mixin_config(self) -> DictConfig:
        """Return the base configuration for the readme mixin test."""
        return {"children": []}

    def _get_test_workdir_class(self) -> type:
        """Return the test class that inherits from WithReadmeWorkdirMixin."""

        @base_class
        class ReadmeWorkdir(WithReadmeWorkdirMixin, BaseClass):
            """Test class that inherits from WithReadmeWorkdirMixin."""

        return ReadmeWorkdir
