from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wexample_config.config_option.abstract_nested_config_option import (
    AbstractNestedConfigOption,
)
from wexample_filestate.option.mixin.option_mixin import OptionMixin
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_config.config_option.abstract_config_option import (
        AbstractConfigOption,
    )
    from wexample_filestate.const.types_state_items import TargetFileOrDirectoryType
    from wexample_filestate.enum.scopes import Scope
    from wexample_filestate.operation.abstract_operation import AbstractOperation


@base_class
class SetupManagerOption(OptionMixin, AbstractNestedConfigOption):
    _allowed_options_cache = None
    _scopes_cache = None

    @classmethod
    def get_scopes(cls) -> list[Scope]:
        cache = cls._scopes_cache
        if cache is None:
            from wexample_filestate.enum.scopes import Scope

            cache = [Scope.LOCATION]
            cls._scopes_cache = cache
        return cache

    @staticmethod
    def get_raw_value_allowed_type() -> Any:
        return dict

    def create_required_operation(
        self, target: TargetFileOrDirectoryType, scopes: set[Scope]
    ) -> AbstractOperation | None:
        return self._create_child_required_operation(target=target, scopes=scopes)

    def get_allowed_options(self) -> list[type[AbstractConfigOption]]:
        cache = SetupManagerOption._allowed_options_cache
        if cache is None:
            from wexample_wex_addon_app.filestate.option._setup_manager.auto_migrate_option import (
                AutoMigrateOption,
            )

            cache = [AutoMigrateOption]
            SetupManagerOption._allowed_options_cache = cache
        return cache
