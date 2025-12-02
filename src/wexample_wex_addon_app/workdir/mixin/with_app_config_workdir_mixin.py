from __future__ import annotations

from tomlkit import TOMLDocument
from wexample_filestate.item.file.structured_content_file import StructuredContentFile
from wexample_helpers.classes.abstract_method import abstract_method
from wexample_helpers.classes.base_class import BaseClass
from wexample_helpers.decorator.base_class import base_class


@base_class
class WithAppConfigWorkdirMixin(BaseClass):
    def get_app_config(self, reload: bool = True) -> TOMLDocument:
        """
        Fetch the data from the pyproject.toml file.
        """
        return self.get_app_config_file(reload=reload).read_parsed()

    @abstract_method
    def get_app_config_file(self, reload: bool = True) -> StructuredContentFile:
        pass
