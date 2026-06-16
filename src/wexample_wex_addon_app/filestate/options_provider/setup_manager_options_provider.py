from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_config.options_provider.abstract_options_provider import (
    AbstractOptionsProvider,
)

if TYPE_CHECKING:
    from wexample_config.config_option.abstract_config_option import (
        AbstractConfigOption,
    )


class SetupManagerOptionsProvider(AbstractOptionsProvider):
    _options_cache: list[type[AbstractConfigOption]] | None = None

    @classmethod
    def get_options(cls) -> list[type[AbstractConfigOption]]:
        if cls._options_cache is None:
            from wexample_wex_addon_app.filestate.option.setup_manager_option import (
                SetupManagerOption,
            )

            cls._options_cache = [SetupManagerOption]
        return cls._options_cache
