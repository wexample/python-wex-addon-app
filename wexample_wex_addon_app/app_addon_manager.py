from functools import cached_property
from typing import TYPE_CHECKING

from wexample_wex_core.common.abstract_addon_manager import AbstractAddonManager

if TYPE_CHECKING:
    from wexample_wex_core.workdir.project_workdir import ProjectWorkdir


class AppAddonManager(AbstractAddonManager):
    @cached_property
    def app_workdir(self) -> "ProjectWorkdir":
        from wexample_wex_addon_app.const.globals import APP_FILE_APP_CONFIG
        from wexample_wex_core.workdir.project_workdir import ProjectWorkdir
        from wexample_helpers.helpers.module import module_load_class_from_file

        path = self.kernel.call_workdir.get_path()
        # Use basic project class to access minimal configuration.
        workdir = ProjectWorkdir.create_from_path(
            path=path,
            io=self.kernel.io,
        )

        manager_config = workdir.get_config().search('files_state.manager')
        if manager_config:
            file_relative = manager_config.get_config_item('file').get_str()
            class_name = manager_config.get_config_item('class').get_str()

            # Compute absolute path to the python file
            file_abs_path = (path / file_relative)

            if file_abs_path.exists():
                # Dynamically load the module and fetch the class
                class_module = module_load_class_from_file(
                    file_path=file_abs_path,
                    class_name=class_name,
                )

                # Good format
                if issubclass(class_module, ProjectWorkdir):
                    # Replace the basic workdir
                    return class_module.create_from_path(
                        path=path,
                        io=self.kernel.io,
                    )
                else:
                    workdir.io.warning(
                        f"Custom class '{class_name}' defined in {APP_FILE_APP_CONFIG} was found at {file_abs_path}, "
                        f"but it must be a subclass of {ProjectWorkdir.__name__}."
                    )
            else:
                workdir.io.warning(
                    f"Custom manager file '{file_relative}' configured in {APP_FILE_APP_CONFIG} "
                    f"does not exist at {file_abs_path}."
                )
        return workdir

