from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_filestate.option.text_option import TextOption
from wexample_filestate.workdir.mixin.with_readme_workdir_mixin import (
    WithReadmeWorkdirMixin,
)
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_addon_app.workdir.mixin.as_suite_package_item import (
    AsSuitePackageItem,
)
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
    def create_from_config(cls, **kwargs) -> AppWorkdirMixin:
        # from wexample_app.const.globals import APP_FILE_APP_CONFIG
        # from wexample_filestate.option.class_option import (
        #     ClassOption,
        # )
        # from wexample_helpers.helpers.module import module_are_same
        #
        # config = kwargs.get("config")

        instance = super().create_from_config(**kwargs)

        # if isinstance(config, dict):
        #     ClassOption.get_name()
        #     preferred = instance.get_preferred_workdir_class()
        #     if preferred:
        #
        #         # The loaded class definition is a different one.
        #         if not module_are_same(preferred, cls):
        #             if not issubclass(preferred, cls):
        #                 io = kwargs.get("io")
        #                 if io:
        #                     io.warning(
        #                         f"Preferred project workdir class '{preferred}' defined in {APP_FILE_APP_CONFIG} "
        #                         f"is not a child of {cls.__name__} as expected by parent workdir."
        #                     )
        #
        #             return preferred.create_from_config(**kwargs)

        return instance

    def get_config(self) -> NestedConfigValue:
        from wexample_config.config_value.nested_config_value import NestedConfigValue

        config_file = self.get_config_file()
        if config_file:
            return config_file.read_config()

        return NestedConfigValue(raw={})

    def get_config_file(self) -> YamlFile:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        config_file = self.find_by_name_recursive(item_name=APP_FILE_APP_CONFIG)
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

    # def get_preferred_workdir_class(self) -> type[ProjectWorkdir] | None:
    #     from wexample_app.const.globals import APP_FILE_APP_CONFIG
    #     from wexample_helpers.helpers.module import (
    #         module_load_class_from_file_with_package_root,
    #     )
    #     from wexample_wex_core.const.globals import WORKDIR_SETUP_DIR
    #
    #     path = self.get_path()
    #     manager_config = self.get_config().search("files_state.manager")
    #
    #     if manager_config:
    #         file_relative = manager_config.get_config_item("file").get_str()
    #         class_name = manager_config.get_config_item("class").get_str()
    #
    #         # Compute absolute path to the python file
    #         file_abs_path = path / file_relative
    #
    #         if file_abs_path.exists():
    #             # Dynamically load the module and fetch the class
    #             class_module = module_load_class_from_file_with_package_root(
    #                 file_path=file_abs_path,
    #                 class_name=class_name,
    #                 # Use the .wex dir as package root so relative imports resolve
    #                 package_root=path / WORKDIR_SETUP_DIR,
    #             )
    #
    #             # Good format
    #             if issubclass(class_module, ProjectWorkdir):
    #                 return class_module
    #             else:
    #                 self.warning(
    #                     f"Custom class '{class_name}' defined in {APP_FILE_APP_CONFIG} was found at {file_abs_path}, "
    #                     f"but it must be a subclass of {ProjectWorkdir.__name__}."
    #                 )
    #         else:
    #             self.warning(
    #                 f"Custom manager file '{file_relative}' configured in {APP_FILE_APP_CONFIG} "
    #                 f"does not exist at {file_abs_path}."
    #             )
    #     return None

    def get_project_name(self) -> str:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        name_config = self.get_config().search("global.name")
        # Ensure we properly handle missing or empty name
        name: str | None = None
        if name_config is not None:
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
            version_config.get_str_or_none() if version_config is not None else None
        )
        if version is None or str(version).strip() == "":
            raise ValueError(
                f"Project at '{self.get_path()}' must define a non-empty 'version' number in {APP_FILE_APP_CONFIG}."
            )
        return str(version).strip()

    def prepare_value(self, raw_value: DictConfig | None = None) -> DictConfig:
        from wexample_filestate.const.disk import DiskItemType
        from wexample_wex_core.const.project import PROJECT_GITIGNORE_DEFAULT

        raw_value = super().prepare_value(raw_value)

        raw_value.update({"mode": {"permissions": "777", "recursive": True}})

        children = raw_value["children"]

        self.append_readme(config=raw_value)
        self.append_version(config=raw_value)

        children.append(
            {
                "name": ".gitignore",
                "type": DiskItemType.FILE,
                "should_exist": True,
                TextOption.get_name(): {"end_new_line": True},
                "should_contain_lines": PROJECT_GITIGNORE_DEFAULT,
            }
        )

        return raw_value
