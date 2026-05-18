from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wexample_config.config_option.abstract_config_option import AbstractConfigOption
from wexample_filestate.option.mixin.option_mixin import OptionMixin
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_filestate.const.types_state_items import TargetFileOrDirectoryType
    from wexample_filestate.enum.scopes import Scope
    from wexample_filestate.operation.abstract_operation import AbstractOperation


@base_class
class AutoMigrateOption(OptionMixin, AbstractConfigOption):
    @classmethod
    def get_scopes(cls) -> list[Scope]:
        from wexample_filestate.enum.scopes import Scope

        return [Scope.LOCATION]

    @staticmethod
    def get_raw_value_allowed_type() -> Any:
        return bool

    def create_required_operation(
        self, target: TargetFileOrDirectoryType, scopes: set[Scope]
    ) -> AbstractOperation | None:
        value = self.get_value()
        if value.is_none() or not value.is_true():
            return None

        # The target's root must be a workdir that supports migrations.
        root = target.get_root()
        from wexample_migration.workdir.mixin.with_migration_workdir_mixin import (
            WithMigrationWorkdirMixin,
        )

        if not isinstance(root, WithMigrationWorkdirMixin):
            return None

        status = root.migration_status(extras={"workdir": root})
        pending = status.get("pending") or []
        if not pending:
            return None

        from wexample_wex_addon_app.filestate.operation.setup_manager_migration_operation import (
            SetupManagerMigrationOperation,
        )

        return SetupManagerMigrationOperation(
            option=self,
            target=target,
            description=f"Apply {len(pending)} pending setup-manager migration(s): {', '.join(pending)}",
        )
