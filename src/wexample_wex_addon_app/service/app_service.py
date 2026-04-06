from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@base_class
class AppService:
    name: str = public_field(description="Service name (e.g. 'mysql')")
    app_workdir: AppWorkdir = public_field(description="The app this service belongs to")
