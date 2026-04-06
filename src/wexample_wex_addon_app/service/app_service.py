from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir


@base_class
class AppService:
    name: str = public_field(description="Service name (e.g. 'mysql')")
    app_workdir: AppWorkdir = public_field(description="The app this service belongs to")
    service_dir: Path | None = public_field(default=None, description="Path to the service directory in the addon package")
    manifest: dict = public_field(factory=dict, description="Parsed service.yml content")

    def get_compose_file(self) -> Path | None:
        if not self.service_dir:
            return None
        compose_rel = self.manifest.get("docker", {}).get("compose")
        if not compose_rel:
            return None
        compose_abs = self.service_dir / compose_rel
        return compose_abs if compose_abs.exists() else None
