from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_filestate.config_value.file_content_config_value import FileContentConfigValue
from wexample_helpers.const.types import FileStringOrPath
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.workdir.mixin.as_suite_package_item import (
    AsSuitePackageItem,
)
from wexample_wex_addon_app.workdir.mixin.with_readme_workdir_mixin import (
    WithReadmeWorkdirMixin,
)
from wexample_wex_core.const.globals import WORKDIR_SETUP_DIR, CORE_DIR_NAME_TMP
from wexample_wex_core.workdir.mixin.with_app_version_workdir_mixin import (
    WithAppVersionWorkdirMixin,
)

if TYPE_CHECKING:
    from wexample_config.config_value.nested_config_value import NestedConfigValue
    from wexample_config.const.types import DictConfig
    from wexample_filestate.item.file.yaml_file import YamlFile


@base_class
class AppWorkdirMixin(
    AsSuitePackageItem, WithReadmeWorkdirMixin, WithAppVersionWorkdirMixin
):
    @classmethod
    def get_config_from_path(cls, path: FileStringOrPath) -> YamlFile | None:
        from wexample_filestate.item.file.yaml_file import YamlFile
        from wexample_app.const.globals import APP_FILE_APP_CONFIG
        setup_config_path = Path(path) / WORKDIR_SETUP_DIR / APP_FILE_APP_CONFIG

        if setup_config_path.exists():
            return YamlFile.create_from_path(
                path=setup_config_path,
            )

        return None

    @classmethod
    def is_app_workdir_path(cls, path: FileStringOrPath) -> bool:
        config = cls.is_app_workdir_path(path=path) is not None
        if config:
            return not config.read_config().search('global.version').is_none()
        return False

    def get_config(self) -> NestedConfigValue:
        from wexample_config.config_value.nested_config_value import NestedConfigValue

        config_file = self.get_config_file()
        if config_file:
            return config_file.read_config()

        return NestedConfigValue(raw={})

    def get_config_file(self) -> YamlFile:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        config_file = self.find_by_path(path=f"{WORKDIR_SETUP_DIR}/{APP_FILE_APP_CONFIG}")
        assert config_file is not None
        return config_file

    def get_env_config(self) -> NestedConfigValue:
        from wexample_config.config_value.nested_config_value import NestedConfigValue
        from wexample_filestate.item.file.env_file import EnvFile
        from wexample_wex_core.const.globals import WORKDIR_SETUP_DIR

        config_dir = self.find_by_name(WORKDIR_SETUP_DIR)
        if config_dir:
            dot_env = config_dir.find_by_name(EnvFile.EXTENSION_DOT_ENV)
            if dot_env:
                return dot_env.read_config()
        return NestedConfigValue(raw={})

    def get_env_parameter(self, key: str, default: str | None = None) -> str | None:
        # Search in .env.
        value = (
            self.get_env_config()
            .get_config_item(key=key, default=default)
            .get_str_or_none()
        )

        if value is None:
            return super().get_env_parameter(
                key=key,
                default=default,
            )

        return value

    def get_project_name(self) -> str:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        name_config = self.get_config().search("global.name")
        # Ensure we properly handle missing or empty name
        name: str | None = None
        if not name_config.is_none():
            name = (name_config.get_str_or_none() or "").strip()
        # Enforce that a project must have a non-empty name; include path for debug
        if not name:
            raise ValueError(
                f"Project at '{self.get_path()}' must define a non-empty 'name' in {APP_FILE_APP_CONFIG}."
            )
        return name

    def get_project_version(self) -> str:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        # Ensure we properly handle missing node and empty value
        config = self.get_config_file().read_config()
        version_config = config.search("global.version")
        version = (
            version_config.get_str_or_none()
        )
        if version is None or str(version).strip() == "":
            raise ValueError(
                f"Project at '{self.get_path()}' must define a non-empty 'version' number in {APP_FILE_APP_CONFIG}."
            )
        return str(version).strip()

    def prepare_value(self, raw_value: DictConfig | None = None) -> DictConfig:
        from wexample_wex_core.const.project import PROJECT_GITIGNORE_DEFAULT
        from wexample_app.const.globals import APP_FILE_APP_CONFIG
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.item.file.env_file import EnvFile
        from wexample_filestate.option.text_option import TextOption
        from wexample_wex_core.const.globals import WORKDIR_SETUP_DIR
        from wexample_filestate.item.file.yaml_file import YamlFile

        raw_value = super().prepare_value(raw_value)

        raw_value.update({"mode": {"permissions": "777", "recursive": True}})

        self.append_readme(config=raw_value)
        self.append_version(config=raw_value)

        import wexample_wex_core
        import importlib.resources
        app_manager_template_path = Path(importlib.resources.files(wexample_wex_core)) / "resources" / "app-manager.sh"

        raw_value["children"].append(
            {
                # .wex
                "name": WORKDIR_SETUP_DIR,
                "type": DiskItemType.DIRECTORY,
                "should_exist": True,
                "children": [
                    {
                        # .env
                        "class": EnvFile,
                        "name": EnvFile.EXTENSION_DOT_ENV,
                        "type": DiskItemType.FILE,
                        "should_exist": True,
                        TextOption.get_name(): {"end_new_line": True},
                    },
                    {
                        # config.yml
                        "name": APP_FILE_APP_CONFIG,
                        "type": DiskItemType.FILE,
                        "should_exist": True,
                        "class": YamlFile,
                        TextOption.get_name(): {"end_new_line": True},
                        "yaml": {"sort_recursive": True},
                    },
                    {
                        # python (app manager)
                        "name": "bin",
                        "type": DiskItemType.DIRECTORY,
                        "should_exist": True,
                        "children": [
                            {
                                "name": "app-manager",
                                "type": DiskItemType.FILE,
                                "should_exist": True,
                                "content": FileContentConfigValue(
                                    path=app_manager_template_path
                                ),
                            }
                        ],
                    },
                    {
                        # tmp
                        "name": CORE_DIR_NAME_TMP,
                        "type": DiskItemType.DIRECTORY,
                        "should_exist": True,
                    },
                    {
                        "name": ".gitignore",
                        "type": DiskItemType.FILE,
                        "should_exist": True,
                        "should_contain_lines": [EnvFile.EXTENSION_DOT_ENV],
                        TextOption.get_name(): {"end_new_line": True},
                    },
                ],
            })

        raw_value["children"].append(
            {
                "name": ".gitignore",
                "type": DiskItemType.FILE,
                "should_exist": True,
                TextOption.get_name(): {"end_new_line": True},
                "should_contain_lines": PROJECT_GITIGNORE_DEFAULT,
            }
        )

        return raw_value
