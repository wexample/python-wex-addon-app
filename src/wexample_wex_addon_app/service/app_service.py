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

    def get_runtime_contribution(self) -> dict:
        """Return this service's contribution to the runtime config.

        Reads service config from config.yml (host, port, name, password, user, ...)
        and compose file path, structured under service.{name}.
        Also resolves declarative runtime.bind paths from service.yml.
        """
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        app_config = self.app_workdir.get_config()
        sconfig = app_config.search(f"service.{self.name}")
        sconfig_dict = sconfig.to_dict() if not sconfig.is_none() else {}

        contribution: dict = {}

        if sconfig_dict:
            contribution["service"] = {self.name: sconfig_dict}

        compose = self.get_compose_file()
        if compose:
            contribution.setdefault("service", {}).setdefault(self.name, {})
            contribution["service"][self.name]["compose"] = str(compose)

        bind_declarations = self.manifest.get("runtime", {}).get("bind", {})
        if bind_declarations:
            env = self.app_workdir.get_app_env() or ""
            wex_dir = self.app_workdir.get_path() / WORKDIR_SETUP_DIR
            resolved_binds = {}
            for key, rel_path in bind_declarations.items():
                env_specific = wex_dir / "env" / env / rel_path
                base = wex_dir / rel_path
                if env_specific.exists():
                    resolved_binds[key] = str(env_specific)
                elif base.exists():
                    resolved_binds[key] = str(base)
                else:
                    raise FileNotFoundError(
                        f"Bind '{key}' declared in service '{self.name}' could not be resolved: "
                        f"neither '{env_specific}' nor '{base}' exists."
                    )
            contribution["bind"] = resolved_binds

        return contribution
