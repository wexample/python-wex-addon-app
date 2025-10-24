from __future__ import annotations

from wexample_helpers.decorator.base_class import base_class
from wexample_wex_core.workdir.workdir import Workdir

from wexample_wex_addon_app.workdir.mixin.app_workdir_mixin import AppWorkdirMixin


@base_class
class BasicAppWorkdir(AppWorkdirMixin, Workdir):
    pass
