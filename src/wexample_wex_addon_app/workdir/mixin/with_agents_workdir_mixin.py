from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig


AGENTS_CONTENT = "This project is managed by the wex script.\n"
CLAUDE_POINTER_CONTENT = "See AGENTS.md — no Claude-specific instructions.\n"


@base_class
class WithAgentsWorkdirMixin(BaseClass):
    def append_agents(self, config: DictConfig | None = None) -> DictConfig:
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.option.text_option import TextOption

        config.get("children").append(
            {
                "name": "AGENTS.md",
                "type": DiskItemType.FILE,
                "should_exist": True,
                "content": AGENTS_CONTENT,
                TextOption.get_name(): {"end_new_line": True},
            }
        )

        config.get("children").append(
            {
                "name": "CLAUDE.md",
                "type": DiskItemType.FILE,
                "should_exist": True,
                "content": CLAUDE_POINTER_CONTENT,
                TextOption.get_name(): {"end_new_line": True},
            }
        )

        return config
