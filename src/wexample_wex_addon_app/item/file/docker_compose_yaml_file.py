from __future__ import annotations

from wexample_filestate.item.file.yaml_file import YamlFile
from wexample_helpers.decorator.base_class import base_class


@base_class
class DockerComposeYamlFile(YamlFile):
    """A docker-compose YAML (base, override, or generated runtime)."""

    def read_container_names(self) -> list[str]:
        """List the resolved container names (falls back to service key)."""
        return [
            attrs.get("container_name", name)
            for name, attrs in self.read_services().items()
        ]

    def read_services(self) -> dict:
        """Return the `services:` dict, or an empty dict if absent."""
        data = self.read_parsed() or {}
        return data.get("services", {}) or {}
