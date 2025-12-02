from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.const.types import FileStringOrPath
from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.common.io_manager import IoManager

if TYPE_CHECKING:
    from wexample_config.config_value.nested_config_value import NestedConfigValue
    from wexample_filestate.item.file.yaml_file import YamlFile


@base_class
class WithAppRegistryMixin(BaseClass):
    @classmethod
    def get_registry_from_path(
        cls, path: FileStringOrPath, io: IoManager
    ) -> YamlFile | None:
        from wexample_filestate.item.file.yaml_file import YamlFile

        registry_path = cls.get_registry_path_from_path(path=path)
        if registry_path.exists():
            return YamlFile.create_from_path(path=registry_path, io=io)
        return None

    @classmethod
    def get_registry_path_from_path(cls, path: FileStringOrPath) -> FileStringOrPath:
        from pathlib import Path

        from wexample_app.const.globals import WORKDIR_SETUP_DIR
        from wexample_wex_core.const.globals import (
            CORE_DIR_NAME_TMP,
            CORE_FILE_NAME_REGISTRY,
        )

        return (
            Path(path) / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / CORE_FILE_NAME_REGISTRY
        )

    def build_registry_value(self) -> NestedConfigValue:
        from wexample_config.config_value.nested_config_value import NestedConfigValue

        return NestedConfigValue(
            raw={
                "config": self.get_config(),
                "env": self.get_app_env(),
            }
        )

    def get_registry(self, rebuild: bool = False) -> NestedConfigValue:
        registry = self.get_registry_file(rebuild=rebuild)
        return registry.read_config()

    def get_registry_file(self, rebuild: bool = False) -> YamlFile:
        from wexample_filestate.item.file.yaml_file import YamlFile

        registry_path = self.get_registry_path_from_path(path=self.get_path())
        registry = YamlFile.create_from_path(path=registry_path, io=self.io)

        if rebuild or not registry.get_path().exists():
            registry.write_config(self.build_registry_value())

        return registry
