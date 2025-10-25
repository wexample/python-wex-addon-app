from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_prompt.common.io_manager import IoManager

from wexample_app.const.globals import (
    APP_FILE_APP_MANAGER,
    APP_PATH_BIN_APP_MANAGER,
    APP_PATH_APP_MANAGER,
)
from wexample_filestate.config_value.file_content_config_value import (
    FileContentConfigValue,
)
from wexample_helpers.const.types import FileStringOrPath
from wexample_helpers.decorator.base_class import base_class
from wexample_helpers.helpers.shell import ShellResult
from wexample_wex_addon_app.app_addon_manager import AppAddonManager
from wexample_wex_addon_app.workdir.mixin.as_suite_package_item import (
    AsSuitePackageItem,
)
from wexample_wex_addon_app.workdir.mixin.with_readme_workdir_mixin import (
    WithReadmeWorkdirMixin,
)
from wexample_wex_core.const.globals import CORE_DIR_NAME_TMP, WORKDIR_SETUP_DIR
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
        config = cls.get_config_from_path(path=path)
        if config:
            return not config.read_config().search("global.version").is_none()
        return False

    @classmethod
    def is_app_workdir_path_setup(cls, path: FileStringOrPath) -> bool:
        path = Path(path)
        if cls.is_app_workdir_path(path=path):
            # app-manager exists.
            return (path / APP_PATH_BIN_APP_MANAGER).exists() and (
                path / APP_PATH_APP_MANAGER / ".venv/bin/python"
            ).exists()
        return False

    @classmethod
    def get_registry_path_from_path(cls, path: FileStringOrPath) -> FileStringOrPath:
        from wexample_wex_core.const.globals import (
            WORKDIR_SETUP_DIR,
            CORE_DIR_NAME_TMP,
            CORE_FILE_NAME_REGISTRY,
        )

        return (
            Path(path) / WORKDIR_SETUP_DIR / CORE_DIR_NAME_TMP / CORE_FILE_NAME_REGISTRY
        )

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
    def shell_run_from_path(
        cls, path: FileStringOrPath, cmd: list[str] | str
    ) -> None | ShellResult:
        from wexample_helpers.helpers.shell import shell_run

        if not isinstance(cmd, list):
            cmd = [cmd]

        if not AppWorkdirMixin.is_app_workdir_path_setup(path=path):
            manager_path = path / APP_PATH_APP_MANAGER
            # This is a non installed app.
            if manager_path.exists():
                # Install it.
                shell_run(
                    cmd=[
                        "pdm",
                        "install",
                    ],
                    cwd=path / APP_PATH_APP_MANAGER,
                    inherit_stdio=True,
                )
            else:
                # This is an undefined directory.
                return None

        full_cmd = [str(APP_PATH_BIN_APP_MANAGER)]
        full_cmd.extend(cmd)

        # Ask parent suite to generate the info registry that contains packages readme information
        return shell_run(
            cmd=full_cmd,
            cwd=path,
            inherit_stdio=True,
        )

    def build_registry_value(self) -> NestedConfigValue:
        from wexample_config.config_value.nested_config_value import NestedConfigValue

        return NestedConfigValue(
            raw={
                "config": self.get_config(),
            }
        )

    def build_registry(self) -> YamlFile:
        from wexample_filestate.item.file.yaml_file import YamlFile

        registry_path = self.get_registry_path_from_path(path=self.get_path())

        registry = YamlFile.create_from_path(path=registry_path, io=self.io)

        registry.write_config(self.build_registry_value())

        return registry

    def get_config(self) -> NestedConfigValue:
        from wexample_config.config_value.nested_config_value import NestedConfigValue

        config_file = self.get_config_file()
        if config_file:
            return config_file.read_config()

        return NestedConfigValue(raw={})

    def get_config_file(self) -> YamlFile:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        config_file = self.find_by_path(
            path=f"{WORKDIR_SETUP_DIR}/{APP_FILE_APP_CONFIG}"
        )
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
        version = version_config.get_str_or_none()
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
                                "name": APP_FILE_APP_MANAGER,
                                "type": DiskItemType.FILE,
                                "should_exist": True,
                                "content": FileContentConfigValue(
                                    path=AppAddonManager.get_shell_manager_path()
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
            }
        )

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
