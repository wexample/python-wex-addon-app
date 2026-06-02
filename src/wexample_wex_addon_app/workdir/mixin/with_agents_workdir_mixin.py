from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig


CLAUDE_POINTER_CONTENT = "See AGENTS.md — no Claude-specific instructions.\n"


def build_agents_content(target) -> str:
    """Return the AGENTS.md content for ``target``.

    Lambda-style builder so per-project substitutions (wex entry command,
    documentation URL, etc.) can be injected here later. For now it just
    returns the static template with TODO placeholders.
    """
    return (
        "This project is managed by the **wex** script.\n"
        "\n"
        "- **With wex installed:** run `TODO` to discover available commands.\n"
        "- **Without wex:** read `.wex/knowledge/__summary.md` for static documentation.\n"
        "- **Unsure?** Run `wex hi` — prints `hi!` if available, "
        "otherwise see https://github.com/wexample/wex/blob/master/README.md.\n"
    )


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
                "content": lambda target: build_agents_content(target),
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
