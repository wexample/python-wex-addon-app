from __future__ import annotations

from typing import TYPE_CHECKING, Any

from wexample_app.const.output import OUTPUT_FORMAT_JSON, OUTPUT_TARGET_FILE
from wexample_app.helpers.request import request_build_id
from wexample_app.item.file.iml_file import ImlFile
from wexample_app.workdir.mixin.with_runtime_config_mixin import WithRuntimeConfigMixin
from wexample_helpers.const.types import FileStringOrPath
from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.common.app_manager_shell_result import AppManagerShellResult
from wexample_wex_core.resolver.addon_command_resolver import AddonCommandResolver
from wexample_wex_core.workdir.mixin.with_app_version_workdir_mixin import (
    WithAppVersionWorkdirMixin,
)
from wexample_wex_core.workdir.workdir import Workdir

from wexample_wex_addon_app.workdir.mixin.with_app_config_workdir_mixin import (
    WithAppConfigWorkdirMixin,
)
from wexample_wex_addon_app.workdir.mixin.with_app_registry_mixin import (
    WithAppRegistryMixin,
)
from wexample_wex_addon_app.workdir.mixin.with_readme_workdir_mixin import (
    WithReadmeWorkdirMixin,
)
from wexample_wex_addon_app.workdir.mixin.with_suite_tree_workdir_mixin import (
    WithSuiteTreeWorkdirMixin,
)

if TYPE_CHECKING:
    from wexample_config.const.types import DictConfig
    from wexample_helpers.classes.shell_result import ShellResult
    from wexample_config.config_value.config_value import ConfigValue

@base_class
class AppWorkdir(
    WithAppConfigWorkdirMixin,
    WithSuiteTreeWorkdirMixin,
    WithReadmeWorkdirMixin,
    WithAppVersionWorkdirMixin,
    WithRuntimeConfigMixin,
    WithAppRegistryMixin,
    Workdir,
):
    @classmethod
    def is_app_workdir_path(cls, path: FileStringOrPath) -> bool:
        config = cls.get_config_from_path(path=path)
        if config:
            return not config.read_config().search("global.version").is_none()
        return False

    @classmethod
    def is_app_workdir_path_setup(cls, path: FileStringOrPath) -> bool:
        from pathlib import Path

        from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

        path = Path(path)
        if cls.is_app_workdir_path(path=path):
            # app-manager exists.
            return (path / APP_PATH_BIN_APP_MANAGER).exists()
        return False

    @classmethod
    def manager_run_command_from_path(
        cls,
        path: str,
        command: callable,
        arguments: list[str] | None = None,
    ) -> AppManagerShellResult:
        """
        Execute a Python addon command (e.g., app__setup__install) using the app manager,
        within a specific workdir.
        """
        from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER
        from wexample_helpers.helpers.shell import shell_run

        # Resolve function to CLI command name
        resolved_command = AddonCommandResolver.build_command_from_function(
            command_wrapper=command
        )

        request_id = request_build_id()

        # Build full command
        cmd = [resolved_command] + (arguments or [])
        full_cmd = [
            str(APP_PATH_BIN_APP_MANAGER),
            "--force-request-id",
            request_id,
            "--output-format",
            OUTPUT_FORMAT_JSON,
            "--output-target",
            OUTPUT_TARGET_FILE,
        ] + cmd

        # Run the manager command in the given workdir
        return AppManagerShellResult.from_shell_result(
            request_id=request_id,
            result=shell_run(cmd=full_cmd, cwd=path, inherit_stdio=True),
        )

    @classmethod
    def manager_run_from_path(
        cls, path: FileStringOrPath, cmd: list[str] | str
    ) -> None | ShellResult:
        from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER
        from wexample_helpers.helpers.shell import shell_run

        if not isinstance(cmd, list):
            cmd = [cmd]

        full_cmd = [str(APP_PATH_BIN_APP_MANAGER)]
        full_cmd.extend(cmd)

        # Ask parent suite to generate the info registry that contains packages readme information
        return shell_run(
            cmd=full_cmd,
            cwd=path,
            inherit_stdio=True,
        )

    @classmethod
    def shell_run_from_path(
        cls, path: FileStringOrPath, cmd: list[str] | str
    ) -> None | ShellResult:
        from wexample_helpers.helpers.shell import shell_run

        return shell_run(
            cmd=cmd,
            cwd=str(path),
            inherit_stdio=True,
        )

    def get_project_name(self) -> str:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        name_config = self.get_runtime_config().search("global.name")
        # Ensure we properly handle missing or empty name
        name: str | None = None
        if not name_config.is_none():
            name = (name_config.get_str_or_none() or "").strip()
        # Enforce that a project must have a non-empty name; include path for debug
        if not name:
            raise ValueError(
                f"Project at '{self.get_path()}' must define a non-empty 'global.name' in {APP_FILE_APP_CONFIG}."
            )
        return name

    def get_project_version(self) -> str:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        # Ensure we properly handle missing node and empty value
        config = self.get_runtime_config()

        version_config = config.search("global.version")
        version = version_config.get_str_or_none()
        if version is None or str(version).strip() == "":
            raise ValueError(
                f"Project at '{self.get_path()}' must define a non-empty 'version' number in {APP_FILE_APP_CONFIG}."
            )
        return str(version).strip()

    def manager_run_command(self, **kwargs) -> AppManagerShellResult:
        return self.manager_run_command_from_path(path=self.get_path(), **kwargs)

    def prepare_value(self, raw_value: DictConfig | None = None) -> DictConfig:
        from wexample_app.const.globals import (
            APP_FILE_APP_CONFIG,
            APP_FILE_APP_MANAGER,
            WORKDIR_SETUP_DIR,
        )
        from wexample_filestate.config_value.file_content_config_value import (
            FileContentConfigValue,
        )
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.item.file.env_file import EnvFile
        from wexample_filestate.item.file.yaml_file import YamlFile
        from wexample_filestate.option.text_option import TextOption
        from wexample_wex_core.const.globals import CORE_DIR_NAME_TMP
        from wexample_wex_core.const.project import PROJECT_GITIGNORE_DEFAULT

        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

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

        raw_value["children"].append(
            {
                # .iml
                "class": self._get_iml_file_class(),
                "name": ImlFile.get_dotted_extension(),
                "type": DiskItemType.FILE,
                "should_exist": True,
            },
        )

        return raw_value

    def shell_run_for_app(self, **kwargs) -> ShellResult:
        return self.shell_run_from_path(path=self.get_path(), **kwargs)

    def _get_iml_file_class(self) -> type[ImlFile]:
        return ImlFile

    def app_install(self, env: str | None = None, force: bool = False) -> bool:
        return True

    def setup_install(self, env: str | None = None, force: bool = False) -> bool:
        from wexample_wex_addon_app.commands.setup.install import app__setup__install

        self.manager_run_command(
            command=app__setup__install,
            arguments=["--env", env] if env else [],
        )

        return True

    def apply(
        self,
        force: bool = False,
        scopes=None,
        filter_path: str | None = None,
        filter_operation: str | None = None,
        max: int = None,
        **kwargs,
    ) -> FileStateResult | None:
        from wexample_wex_addon_app.commands.file_state.rectify import (
            app__file_state__rectify,
        )

        args = []
        if force:
            args.append("--force")

        if filter_path:
            args.extend(["--filter-path", filter_path])

        if filter_operation:
            args.extend(["--filter-operation", filter_operation])

        return self.manager_run_command(
            command=app__file_state__rectify,
            arguments=args,
        ).get_output()

    def configure(self, config: DictConfig) -> None:
        super().configure(config=config)

        self._init_env(env_dict=self.get_env_parameters().to_dict())

    def get_app_env(self) -> str | None:
        from wexample_app.const.env import ENV_NAME_PROD

        return (
            self.get_config().search("env").get_str_or_none()
            or self.get_runtime_config().search("env").get_str_or_none()
            or ENV_NAME_PROD
        )

    def set_app_env(self, env: str | None) -> None:
        from wexample_wex_addon_app.commands.config.update import app__config__update

        self.manager_run_command(
            command=app__config__update,
            arguments=["--env", env] if env else [],
        )

    def ensure_app_manager(self) -> None:
        from wexample_app.const.globals import APP_PATH_APP_MANAGER

        if not (self.get_path() / APP_PATH_APP_MANAGER).exists():
            self.apply()

    def ensure_app_manager_setup(self) -> None:
        if not self.is_app_workdir_path_setup(path=self.get_path()):
            self.setup_install()

    def search_closest_app_manager_bin_path(self) -> Path | None:
        def _test_path(workdir):
            from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

            bin_path = workdir.get_path() / APP_PATH_BIN_APP_MANAGER
            return bin_path if bin_path.exists() else None

        return self.search_closest_parent_workdir(
            callback=_test_path,
        )

    def search_app_or_suite_runtime_config(self, key_path: str, default: Any = None) -> Any:
        def _test_path(workdir):
            val = workdir.get_runtime_config().search(key_path).get_value()
            return val if val is not None else None

        return self.search_closest_parent_workdir(
            callback=_test_path,
        ) or default

    def libraries_sync(self) -> None:
        from wexample_wex_addon_app.commands.dependencies.publish import (
            app__dependencies__publish,
        )

        for library_path_config in (
            self.get_runtime_config().search("libraries").get_list_or_default(default=[])
        ):
            self.log(f"Searching in @path{{{library_path_config.get_str()}}}")

            if AppWorkdir.is_app_workdir_path(
                path=library_path_config.get_str()
            ):
                publishable_dependencies = (
                    AppWorkdir.manager_run_command_from_path(
                        command=app__dependencies__publish,
                        path=library_path_config.get_str(),
                    ).get_output()
                )

                self.update_dependencies(publishable_dependencies)
        self.io.success("All libraries versions are up to date.")

    def get_local_libraries_paths(self) -> list[ConfigValue]:
        return self.get_runtime_config().search(f"libraries").get_list_or_default()
