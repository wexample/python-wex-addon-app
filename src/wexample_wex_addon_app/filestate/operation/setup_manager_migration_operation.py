from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_filestate.operation.abstract_operation import AbstractOperation
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_filestate.enum.scopes import Scope


@base_class
class SetupManagerMigrationOperation(AbstractOperation):
    @classmethod
    def get_scopes(cls) -> list[Scope]:
        from wexample_filestate.enum.scopes import Scope

        return [Scope.LOCATION]

    def apply_operation(self) -> None:
        from wexample_wex_addon_app.commands.migration.run import app__migration__run

        # Root is the workdir itself (ManagedWorkdir), which carries manager_run_command.
        self.target.get_root().manager_run_command(command=app__migration__run)

    def undo(self) -> None:
        # Migrations are not reversed automatically: each migration's own
        # rollback path goes through `app::migration/rollback`.
        pass
