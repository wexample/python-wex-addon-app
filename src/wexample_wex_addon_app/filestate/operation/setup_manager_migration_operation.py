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
        # In-process: skip subprocess + binary dependency. Calls the same path
        # as `app__migration__run` would, minus the command wrapper.
        root = self.target.get_root()
        root.migration_run(extras={"workdir": root})

    def undo(self) -> None:
        # Migrations are not reversed automatically: each migration's own
        # rollback path goes through `app::migration/rollback`.
        pass
