from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import TYPE_CHECKING, Any

from wexample_app.const.output import OUTPUT_FORMAT_JSON, OUTPUT_TARGET_FILE
from wexample_app.helper.request import request_build_id
from wexample_app.item.file.iml_file import ImlFile
from wexample_app.workdir.mixin.with_local_data_mixin import WithLocalDataMixin
from wexample_app.workdir.mixin.with_runtime_config_mixin import WithRuntimeConfigMixin
from wexample_filestate.item.mixin.with_runners_root_mixin import WithRunnersRootMixin
from wexample_helpers.const.types import FileStringOrPath
from wexample_helpers.decorator.base_class import base_class
from wexample_migration.abstract_migration import AbstractMigration
from wexample_migration.workdir.mixin.with_migration_workdir_mixin import (
    WithMigrationWorkdirMixin,
)
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
    from pathlib import Path

    from wexample_config.config_value.config_value import ConfigValue
    from wexample_config.const.types import DictConfig
    from wexample_config.options_provider.abstract_options_provider import (
        AbstractOptionsProvider,
    )
    from wexample_helpers.classes.shell_result import ShellResult


@base_class
class ManagedWorkdir(
    WithMigrationWorkdirMixin,
    WithRunnersRootMixin,
    WithAppConfigWorkdirMixin,
    WithSuiteTreeWorkdirMixin,
    WithReadmeWorkdirMixin,
    WithAppVersionWorkdirMixin,
    WithRuntimeConfigMixin,
    WithAppRegistryMixin,
    WithLocalDataMixin,
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
        from wexample_helpers.helper.shell import shell_run

        # Resolve function to CLI command name
        resolved_command = AddonCommandResolver.build_command_from_function(
            command_wrapper=command
        )

        request_id = request_build_id()

        # Build full command (inline resolved_command + arguments to avoid two
        # intermediate list allocations from the previous split construction)
        full_cmd = [
            str(APP_PATH_BIN_APP_MANAGER),
            "--force-request-id",
            request_id,
            "--output-format",
            OUTPUT_FORMAT_JSON,
            "--output-target",
            OUTPUT_TARGET_FILE,
            "--subprocess",
            resolved_command,
            *(arguments or []),
        ]

        # Run the manager command in the given workdir
        return AppManagerShellResult.from_shell_result(
            request_id=request_id,
            result=shell_run(cmd=full_cmd, cwd=path, inherit_stdio=True),
        )

    @classmethod
    def manager_run_from_path(
        cls,
        path: FileStringOrPath,
        cmd: list[str] | str,
        inherit_stdio: bool = True,
    ) -> ShellResult:
        from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER
        from wexample_helpers.helper.shell import shell_run

        if not isinstance(cmd, list):
            cmd = [cmd]

        full_cmd = [str(APP_PATH_BIN_APP_MANAGER), "--subprocess"]
        full_cmd.extend(cmd)

        return shell_run(
            cmd=full_cmd,
            cwd=path,
            inherit_stdio=inherit_stdio,
        )

    @classmethod
    def shell_run_from_path(
        cls, path: FileStringOrPath, cmd: list[str] | str
    ) -> ShellResult:
        from wexample_helpers.helper.shell import shell_run

        return shell_run(
            cmd=cmd,
            cwd=str(path),
            inherit_stdio=True,
        )

    @staticmethod
    def _migration_version_key(migration_class: type[AbstractMigration]):
        from wexample_migration.migration_stamp import stamp_sort_key

        return stamp_sort_key(migration_class.VERSION, migration_class.SEQ)

    def add_gitignore_rules(
        self,
        children: list[dict],
        *lines: str,
        section: str | None = None,
    ) -> dict:
        """Ensure the `.gitignore` config in `children` has the given lines.

        - Creates the .gitignore config (file, should_exist, end_new_line)
          if absent, so callers never have to repeat the boilerplate.
        - Idempotently enables the GitignoreOption rectifier
          (`gitignore: True`) so the file is dedup+sorted on every pass.
        - The `section` parameter is kept for caller intent (the call site
          documents which language/topic the lines belong to) but is
          intentionally NOT injected into `should_contain_lines`. Section
          headers via that mechanism produce orphan `# Section` lines at
          end-of-file whenever the entries are already present somewhere
          else in the file. Real section grouping belongs to the rectifier
          and will be plumbed through when it supports glob-aware
          organization.

        Returns the .gitignore config dict so the caller can attach extra
        keys (e.g. specific TextOption tweaks) if needed.
        """
        del section  # accepted for caller intent; not used yet (see docstring)
        from wexample_filestate.const.disk import DiskItemType
        from wexample_filestate.option.text_option import TextOption
        from wexample_helpers.helper.array import array_dict_get_by

        config = array_dict_get_by("name", ".gitignore", children)
        if config is None:
            config = {
                "name": ".gitignore",
                "type": DiskItemType.FILE,
                "should_exist": True,
                TextOption.get_name(): {"end_new_line": True},
            }
            children.append(config)

        config.setdefault("gitignore", True)
        bucket = config.setdefault("should_contain_lines", [])
        bucket.extend(lines)
        return config

    def app_install(self, env: str | None = None, force: bool = False) -> bool:
        return True

    def apply(
        self,
        force: bool = False,
        scopes=None,
        filter_paths: list[str] | None = None,
        filter_operation: str | None = None,
        max: int = None,
        **kwargs,
    ) -> FileStateResult | None:
        from wexample_wex_addon_app.commands.state.rectify import (
            app__state__rectify,
        )

        args = []
        if force:
            args.append("--force")

        if filter_paths:
            for p in filter_paths:
                args.extend(["--filter-path", p])

        if filter_operation:
            args.extend(["--filter-operation", filter_operation])

        return self.manager_run_command(
            command=app__state__rectify,
            arguments=args,
        ).get_output()

    def build_runtime_config_value(self) -> NestedConfigValue:
        from wexample_config.config_value.nested_config_value import NestedConfigValue
        from wexample_helpers.helper.dict import dict_merge

        base = super().build_runtime_config_value()
        project_name = self.get_docker_project_name(self.get_app_env())
        return NestedConfigValue(
            raw=dict_merge(base.to_dict(), {"app": {"project_name": project_name}})
        )

    def clear_logs(self) -> None:
        import shutil

        from wexample_app.const.path import APP_DIR_NAME_TMP

        logs_dir = self.get_path() / APP_DIR_NAME_TMP / "logs"
        if logs_dir.exists():
            shutil.rmtree(logs_dir)

    def configure(self, config: DictConfig, eager: bool = False) -> None:
        super().configure(config=config, eager=eager)

        self._init_env(env_dict=self.get_env_parameters().to_dict())

    def docker_build_long_container_name(self, container_name: str) -> str:
        project_name = (
            self.get_runtime_config().search("app.project_name").get_str_or_none()
        )
        if not project_name:
            project_name = self.get_docker_project_name()
        return f"{project_name}_{container_name}"

    def ensure_app_manager(self) -> None:
        from wexample_app.const.globals import APP_PATH_APP_MANAGER

        if not (self.get_path() / APP_PATH_APP_MANAGER).exists():
            self.apply()

    def ensure_app_manager_setup(self) -> None:
        if not self.is_app_workdir_path_setup(path=self.get_path()):
            self.setup_install()

    def ensure_manager_bin(self) -> bool:
        """Ensure `.wex/bin/app-manager` exists as a self-contained executable.

        Replaces broken symlinks or stale content and sets the executable bit.
        Returns True if a write happened, False if already OK.
        """
        import stat

        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        template_content = AppAddonManager.get_shell_manager_path().read_text()
        bin_path = self.get_path() / ".wex" / "bin" / "app-manager"

        needs_write = True
        if bin_path.is_file() and not bin_path.is_symlink():
            try:
                if bin_path.read_text() == template_content:
                    needs_write = False
            except OSError:
                pass

        if needs_write:
            bin_path.parent.mkdir(parents=True, exist_ok=True)
            if bin_path.is_symlink() or bin_path.exists():
                bin_path.unlink()
            bin_path.write_text(template_content)

        mode = bin_path.stat().st_mode
        bin_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        return needs_write

    def get_app_env(self) -> str | None:
        from wexample_app.const.env import ENV_NAME_PROD

        # Must NOT call get_runtime_config() here — it would create a circular dependency:
        # get_runtime_config() → build_runtime_config_value() → get_app_env() → get_runtime_config()
        # APP_ENV is always set via .wex/local/env.yml — never in config.yml (which uses "env:" as a block).
        return self.get_env_parameter("APP_ENV", default=None) or ENV_NAME_PROD
    def get_code_paths(self) -> list[Path]:
        """Paths a cross-codebase tool (refactor, lint sweep, …) should treat
        as this workdir's source roots.

        Default for an app: the workdir itself. Subclasses that aggregate
        children (suite → packages, master → apps) override this to expand
        polymorphically — callers never branch on workdir type.
        """
        return [self.get_path()]

    def get_code_scope_paths(self, kernel) -> list[Path]:
        """Full set of code paths reachable from this workdir for ops that
        cross workdir boundaries (refactor, sweep, …).

        Default: if contained in a parent that knows how to expand a scope
        (e.g. a suite that knows its packages + consumers), delegate to it.
        Otherwise fall back to this workdir's own code paths.
        """
        from wexample_wex_addon_app.app_addon_manager import AppAddonManager

        suite_path = self.find_suite_workdir_path()
        if suite_path is None or suite_path == self.get_path():
            return self.get_code_paths()
        suite = AppAddonManager.from_kernel(kernel).create_app_workdir(path=suite_path)
        return suite.get_code_scope_paths(kernel)

    def get_dependencies_versions(self) -> dict[str, str]:
        return {}

    def get_docker_project_name(self, env: str | None = None) -> str:
        """Single source of truth for the Docker Compose project name.

        Docker container names follow `<project_name>_<service>`. Anything
        that constructs a container name (`docker exec`, runtime config,
        `docker compose --project-name`) MUST go through this method, or
        the two sides will diverge (e.g. `bdo-letters_local_vite` from
        compose vs `bdo_letters_local_vite` from exec).
        """
        from wexample_helpers.helper.string import string_to_snake_case

        name = string_to_snake_case(self.get_project_name())
        if env is None:
            return name
        return f"{name}_{env}"

    def get_domains_config(self) -> dict[str, str | list[str]]:
        app_config = self.get_runtime_app_config()
        domain = app_config.get("domain")

        configured_domains = app_config.get("domains")
        if isinstance(configured_domains, list) and configured_domains:
            domains = [d for d in configured_domains if d]
        elif domain:
            domains = [domain]
        else:
            domains = []

        result: dict[str, str | list[str]] = {}
        if domain:
            result["domain"] = domain
        if domains:
            result["domains"] = domains
            result["domains_string"] = ",".join(domains)

        return result

    def get_local_libraries_paths(self) -> list[ConfigValue]:
        return self.get_runtime_config().search("libraries").get_list_or_default()

    def get_main_container_name(self) -> str:
        config = self.get_runtime_config().search("docker.main_container")
        if not config.is_none():
            return config.get_str()
        main_service = self.get_main_service()
        if main_service:
            return main_service
        raise ValueError(
            "No main container configured (docker.main_container or global.main_service)"
        )

    def get_main_db_service(self) -> str | None:
        return self.get_config().search("docker.db.main").get_str_or_none()

    def get_main_service(self) -> str | None:
        config = self.get_runtime_config().search("global.main_service")
        return config.get_str_or_none() if not config.is_none() else None

    def get_migrations(self):
        package = importlib.import_module("wexample_wex_addon_app.migrations")
        migrations: list[type[AbstractMigration]] = []

        for module_info in pkgutil.iter_modules(package.__path__):
            if module_info.name.startswith("_"):
                continue

            module = importlib.import_module(
                f"wexample_wex_addon_app.migrations.{module_info.name}"
            )

            for _, migration_class in inspect.getmembers(module, inspect.isclass):
                # Cheapest guard first: skip anything not defined in this
                # module (also implicitly excludes AbstractMigration itself,
                # which lives in wexample_migration.abstract_migration).
                if migration_class.__module__ != module.__name__:
                    continue
                if not issubclass(migration_class, AbstractMigration):
                    continue

                migrations.append(migration_class)

        return sorted(migrations, key=self._migration_version_key)

    def get_options_providers(self) -> list[type[AbstractOptionsProvider]]:
        from wexample_filestate_git.options_provider.git_options_provider import (
            GitOptionsProvider,
        )

        from wexample_wex_addon_app.filestate.options_provider.setup_manager_options_provider import (
            SetupManagerOptionsProvider,
        )

        # GitOptionsProvider lives here (not just on CodeBaseWorkdir) because
        # the .gitignore declarations injected in prepare_value carry
        # `gitignore: True`, and the corresponding GitignoreOption must be
        # resolvable on every ManagedWorkdir, not only on code repos.
        return [
            *super().get_options_providers(),
            SetupManagerOptionsProvider,
            GitOptionsProvider,
        ]

    def get_project_name(self) -> str:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        name_config = self.get_config().search("global.name")
        name: str | None = None
        if not name_config.is_none():
            name = (name_config.get_str_or_none() or "").strip()
        if not name:
            raise ValueError(
                f"Project at '{self.get_path()}' must define a non-empty 'global.name' in {APP_FILE_APP_CONFIG}."
            )
        return name

    def get_public_remote_repository_url(self) -> str | None:
        return None

    def get_runtime_app_config(self) -> dict:
        from wexample_helpers.helper.dict import dict_merge

        env = self.get_app_env()
        app_config = dict_merge(
            self.get_config().to_dict(),
            self.get_config(env_name=env).to_dict_or_none() or {},
        )

        env_block = app_config.pop("env", {})
        app_config.update(env_block.get(env, {}))

        return app_config

    def get_service_shell(self, service: str | None = None) -> str:
        config = self.get_runtime_config().search("docker.main_container_shell")
        if not config.is_none():
            return config.get_str()
        return "/bin/bash"

    def get_setup_version(self) -> str:
        from wexample_app.const.globals import APP_FILE_APP_CONFIG

        version_config = self.get_config().search("global.version")
        version = version_config.get_str_or_none()
        if version is None or str(version).strip() == "":
            raise ValueError(
                f"Project at '{self.get_path()}' must define a non-empty 'version' number in {APP_FILE_APP_CONFIG}."
            )
        return str(version).strip()

    def libraries_sync(self) -> None:
        from wexample_wex_addon_app.commands.dependency.publish import (
            app__dependency__publish,
        )

        for library_path_config in (
            self.get_runtime_config()
            .search("libraries")
            .get_list_or_default(default=[])
        ):
            self.log(f"Searching in @path{{{library_path_config.get_str()}}}")

            if ManagedWorkdir.is_app_workdir_path(path=library_path_config.get_str()):
                publishable_dependencies = ManagedWorkdir.manager_run_command_from_path(
                    command=app__dependency__publish,
                    path=library_path_config.get_str(),
                ).get_output()

                self.update_dependencies(publishable_dependencies)
        self.io.success("All libraries versions are up to date.")

    def manager_run(self, cmd: list[str] | str) -> ShellResult:
        return self.manager_run_from_path(path=self.get_path(), cmd=cmd)

    def manager_run_command(self, **kwargs) -> AppManagerShellResult:
        return self.manager_run_command_from_path(path=self.get_path(), **kwargs)

    def migration_read_stamp(self):
        from wexample_migration.migration_stamp import MigrationStamp

        config = self.get_config()
        version = config.search("wex.version").get_str_or_none()
        if version is None or str(version).strip() == "":
            return None

        seq = config.search("wex.migration").get_int_or_none()

        return MigrationStamp(version=str(version).strip(), seq=seq)

    def migration_write_stamp(self, stamp) -> None:
        config_file = self.get_config_file()
        cfg = config_file.read_config()
        cfg.set_by_path("wex.version", stamp.version)
        if stamp.seq is not None:
            cfg.set_by_path("wex.migration", stamp.seq)
        config_file.write_config(cfg)

    def prepare_value(self, raw_value: DictConfig | None = None) -> DictConfig:
        from wexample_app.const.globals import (
            APP_FILE_APP_CONFIG,
            APP_FILE_APP_MANAGER,
            APP_PATH_APP_MANAGER,
            WORKDIR_LOCAL_DIR_NAME,
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

        # Auto-apply pending setup-manager migrations during rectify. Override
        # in user config.yml with `setup_manager: {auto_migrate: false}` to disable.
        raw_value.setdefault("setup_manager", {"auto_migrate": True})

        self.append_readme(config=raw_value)
        self.append_version(config=raw_value)

        gitkeep_child = [
            {
                "name": ".gitkeep",
                "type": DiskItemType.FILE,
                "should_exist": True,
            }
        ]

        raw_value["children"].append(
            {
                # .wex
                "name": WORKDIR_SETUP_DIR,
                "type": DiskItemType.DIRECTORY,
                "should_exist": True,
                "children": [
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
                        # bin (app-manager shell entrypoint)
                        "name": "bin",
                        "type": DiskItemType.DIRECTORY,
                        "should_exist": True,
                        "children": [
                            {
                                "name": APP_FILE_APP_MANAGER,
                                "type": DiskItemType.FILE,
                                "should_exist": True,
                                "mode": {"permissions": "755"},
                                "content": FileContentConfigValue(
                                    path=AppAddonManager.get_shell_manager_path()
                                ),
                            }
                        ],
                    },
                    {
                        # python — Python wex CLI install (venv + PDM). The
                        # `app_manager/` subdir is created by the install
                        # machinery (not filestate), but the .gitignore files
                        # are declared here so committed state stays clean.
                        "name": APP_PATH_APP_MANAGER.parts[1],  # "python"
                        "type": DiskItemType.DIRECTORY,
                        "should_exist": True,
                        "children": [
                            {
                                "name": ".gitignore",
                                "type": DiskItemType.FILE,
                                "should_exist": True,
                                "should_contain_lines": [
                                    "/venv/",
                                ],
                                TextOption.get_name(): {"end_new_line": True},
                                "gitignore": True,
                            },
                            {
                                "name": APP_PATH_APP_MANAGER.parts[2],  # "app_manager"
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                                "children": [
                                    {
                                        "name": ".gitignore",
                                        "type": DiskItemType.FILE,
                                        "should_exist": True,
                                        "should_contain_lines": [
                                            "*.py[cod]",
                                            "__pycache__/",
                                            ".mypy_cache/",
                                            ".pytest_cache/",
                                            ".ruff_cache/",
                                            ".pdm-python",
                                            "/tmp/",
                                            "/logs/",
                                        ],
                                        TextOption.get_name(): {"end_new_line": True},
                                        "gitignore": True,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        # tmp
                        "name": CORE_DIR_NAME_TMP,
                        "type": DiskItemType.DIRECTORY,
                        "should_exist": True,
                        "children": [
                            {
                                # output
                                "name": "output",
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                            },
                        ],
                    },
                    {
                        "name": "knowledge",
                        "type": DiskItemType.DIRECTORY,
                        "should_exist": True,
                        "children": [
                            {
                                "name": "__entrypoint.md",
                                "type": DiskItemType.FILE,
                                "should_exist": True,
                            },
                            {
                                "name": "documents",
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                                "children": [
                                    {
                                        "name": "readme",
                                        "type": DiskItemType.DIRECTORY,
                                        "should_exist": True,
                                        "children": gitkeep_child,
                                    },
                                    {
                                        "name": "agents",
                                        "type": DiskItemType.DIRECTORY,
                                        "should_exist": True,
                                        "children": gitkeep_child,
                                    },
                                ],
                            },
                            {
                                "name": "usage",
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                                "children": gitkeep_child,
                            },
                            {
                                "name": "contributing",
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                                "children": gitkeep_child,
                            },
                            {
                                "name": "specifications",
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                                "children": gitkeep_child,
                            },
                            {
                                "name": "roadmap",
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                                "children": [
                                    {
                                        "name": "todo",
                                        "type": DiskItemType.DIRECTORY,
                                        "should_exist": True,
                                        "children": gitkeep_child,
                                    },
                                    {
                                        "name": "done",
                                        "type": DiskItemType.DIRECTORY,
                                        "should_exist": True,
                                        "children": gitkeep_child,
                                    },
                                    {
                                        "name": "decisions",
                                        "type": DiskItemType.DIRECTORY,
                                        "should_exist": True,
                                        "children": gitkeep_child,
                                    },
                                ],
                            },
                            {
                                "name": CORE_DIR_NAME_TMP,
                                "type": DiskItemType.DIRECTORY,
                                "should_exist": True,
                            },
                        ],
                    },
                    {
                        # local — machine-specific state, never committed
                        "name": WORKDIR_LOCAL_DIR_NAME,
                        "type": DiskItemType.DIRECTORY,
                        "should_exist": True,
                        "children": [
                            {
                                "name": ".gitignore",
                                "type": DiskItemType.FILE,
                                "should_exist": True,
                                "should_contain_lines": [
                                    "*",
                                    ".gitignore",
                                ],
                                TextOption.get_name(): {"end_new_line": True},
                                "gitignore": True,
                            },
                        ],
                    },
                    {
                        "name": ".gitignore",
                        "type": DiskItemType.FILE,
                        "should_exist": True,
                        "should_contain_lines": [
                            "/" + EnvFile.EXTENSION_DOT_ENV,
                            "/" + str(CORE_DIR_NAME_TMP) + "/",
                            f"/{WORKDIR_LOCAL_DIR_NAME}/",
                        ],
                        TextOption.get_name(): {"end_new_line": True},
                        "gitignore": True,
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
                "gitignore": True,
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

    def runtime_cleanup(self) -> tuple[int, int]:
        from wexample_helpers.helper.docker import (
            docker_container_is_running,
            docker_image_exists,
            docker_remove_container,
            docker_remove_image,
            docker_stop_container,
        )
        from wexample_helpers.helper.shell import shell_run

        image_names: set[str] = self._collect_docker_image_names()

        result = shell_run(
            cmd=["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Image}}"],
            capture=True,
        )
        # Avoid splitting each matching line twice by capturing the split result
        # once via a nested loop.
        containers_to_remove = [
            parts[0]
            for line in result.stdout.strip().splitlines()
            if "\t" in line
            for parts in (line.split("\t"),)
            if parts[1] in image_names
        ]

        removed_containers = 0
        for name in containers_to_remove:
            if docker_container_is_running(name):
                docker_stop_container(name)
            docker_remove_container(name)
            removed_containers += 1

        removed_images = 0
        for image_name in image_names:
            if docker_image_exists(image_name):
                docker_remove_image(image_name)
                removed_images += 1

        return removed_containers, removed_images

    def search_app_or_suite_runtime_config(
        self, key_path: str, default: Any = None
    ) -> ConfigValue:
        from wexample_config.config_value.config_value import ConfigValue

        def _test_path(workdir) -> ConfigValue | None:
            config = workdir.get_runtime_config().search(path=key_path)
            if not config.is_none():
                return config
            return None

        return self.search_closest_in_suites_tree(callback=_test_path) or ConfigValue(
            raw=default
        )

    def search_closest_app_manager_bin_path(self) -> Path | None:
        def _test_path(workdir):
            from wexample_app.const.globals import APP_PATH_BIN_APP_MANAGER

            bin_path = workdir.get_path() / APP_PATH_BIN_APP_MANAGER
            return bin_path if bin_path.exists() else None

        return self.search_closest_in_suites_tree(callback=_test_path)

    def set_app_env(self, env: str | None) -> None:
        from wexample_app.const.globals import ENV_VAR_NAME_APP_ENV

        self.set_env_parameter(key=ENV_VAR_NAME_APP_ENV, value=env)
        self.get_registry(rebuild=True)

    def setup_install(self, env: str | None = None, force: bool = False) -> bool:
        return self.app_install(env=env, force=force)

    def shell_run_for_app(self, **kwargs) -> ShellResult:
        return self.shell_run_from_path(path=self.get_path(), **kwargs)

    def _collect_docker_image_names(self) -> set[str]:
        return {
            name
            for provider in self.get_options_providers()
            if (name := provider.get_docker_image_name()) is not None
        }

    def _get_iml_file_class(self) -> type[ImlFile]:
        return ImlFile
