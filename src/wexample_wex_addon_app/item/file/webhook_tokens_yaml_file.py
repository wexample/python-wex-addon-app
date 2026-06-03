from __future__ import annotations

from wexample_filestate.item.file.yaml_file import YamlFile
from wexample_helpers.decorator.base_class import base_class


@base_class
class WebhookTokensYamlFile(YamlFile):
    """An app `.wex/local/webhook_tokens.yml`: per-command webhook tokens."""

    def get_token(self, command_str: str) -> str | None:
        try:
            data = self.read_parsed(strict=False) or {}
        except Exception:
            return None
        return data.get(command_str)
