from __future__ import annotations

from wexample_filestate.item.file.yaml_file import YamlFile
from wexample_helpers.decorator.base_class import base_class


@base_class
class AppRegistryYamlFile(YamlFile):
    """A wex app `.wex/tmp/registry.yml`: built snapshot of resolved config + env."""
