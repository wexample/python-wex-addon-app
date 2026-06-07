from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_wex_addon_app.app_addon_manager import AppAddonManager
    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@base_class
class AppService:
    addon_manager: AppAddonManager = public_field(
        description="Manager used to resolve service dirs and manifests"
    )
    app_workdir: ManagedWorkdir = public_field(
        description="The app this service belongs to"
    )
    manifest: dict = public_field(
        factory=dict, description="Parsed service.yml content"
    )
    name: str = public_field(description="Service name (e.g. 'mysql')")
    service_dir: Path | None = public_field(
        default=None, description="Path to the service directory in the addon package"
    )

    @property
    def address_name(self) -> str:
        """Kebab-case form used in command addresses (`@<service>::...`).

        The CLI command pattern only accepts hyphens, so multi-word service
        names like `gitlab_runner` must be normalized before being interpolated
        into a command string.
        """
        from wexample_helpers.helpers.string import string_to_kebab_case

        return string_to_kebab_case(self.name)

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

        Adds the resolved compose file paths (and env-specific overrides) under
        service.{name}.compose / .compose_env_X, and resolves declarative
        runtime.bind paths from service.yml.

        Note: the service's own config (host, port, password, ...) is NOT
        re-injected here — it's already in the runtime config built by
        `build_runtime_config_value()` (which reads config.yml AND interpolates
        ${VAR} from env). Re-injecting raw config.yml here would overwrite
        interpolated values with literal ${VAR}.
        """
        from wexample_app.const.globals import WORKDIR_SETUP_DIR

        contribution: dict = {}
        env = self.app_workdir.get_app_env() or ""

        for inherited_service_name in self.addon_manager.get_service_inheritance_chain(
            self.name
        ):
            service_dir = self.addon_manager.find_service_dir(inherited_service_name)
            if not service_dir:
                continue
            manifest = self.addon_manager.get_service_manifest_raw(
                inherited_service_name
            )

            compose_rel = manifest.get("docker", {}).get("compose")
            if compose_rel:
                compose_abs = service_dir / compose_rel
                if compose_abs.exists():
                    contribution.setdefault("service", {}).setdefault(
                        inherited_service_name, {}
                    )
                    contribution["service"][inherited_service_name]["compose"] = str(
                        compose_abs
                    )

            env_compose = service_dir / "env" / env / "docker" / "docker-compose.yml"
            if env_compose.exists():
                contribution.setdefault("service", {}).setdefault(
                    inherited_service_name, {}
                )
                contribution["service"][inherited_service_name][
                    f"compose_env_{env}"
                ] = str(env_compose)

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

    def get_vars(self) -> dict[str, dict]:
        """Return the vars declared in service.yml under the `vars:` key.

        Each entry is a dict with optional keys:
          - required (bool): var must be present before app/start
          - generated (bool): skip interactive prompt; install.py handles generation
          - default (str): written to .env without prompt if the key is absent
          - description (str): shown during prompt or in service/vars/list
        """
        return self.manifest.get("vars", {})

    def get_workdir_contribution(self, workdir: ManagedWorkdir) -> dict | None:
        return None
