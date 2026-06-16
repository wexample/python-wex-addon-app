from __future__ import annotations

from pathlib import Path

APPS_BASE_PATH: str = "/var/www"


class AppWebhookTypeResolver:
    """Resolve webhook command, cwd and token for app-type URLs.

    URL format: /webhook/app/{env}/{app_name}/{command/path}
    Token file: {app_path}/.wex/local/webhook_tokens.yml
    """

    def __init__(self, apps_base_path: str = APPS_BASE_PATH) -> None:
        self._base = Path(apps_base_path)

    def build_command(self, command_path: str) -> str | None:
        parsed = self._parse(command_path)
        if parsed is None:
            return None
        _, _, local_command = parsed
        return f".{local_command}"

    def _resolve_app_path(self, command_path: str) -> Path | None:
        """Return the resolved app directory as a Path, or None on bad input."""
        parsed = self._parse(command_path)
        if parsed is None:
            return None
        env, app_name, _ = parsed
        return self._base / env / app_name

    def resolve_cwd(
        self,
        command_path: str,
        query_params: dict[str, list[str]] | None = None,
    ) -> str | None:
        app_path = self._resolve_app_path(command_path)
        return str(app_path) if app_path is not None else None

    def resolve_token(self, command_path: str, command_str: str) -> str | None:
        from wexample_app.const.globals import WORKDIR_LOCAL_DIR_NAME, WORKDIR_SETUP_DIR

        from wexample_wex_addon_app.item.file.webhook_tokens_yaml_file import (
            WebhookTokensYamlFile,
        )

        app_path = self._resolve_app_path(command_path)
        if app_path is None:
            return None
        token_file = app_path / WORKDIR_SETUP_DIR / WORKDIR_LOCAL_DIR_NAME / "webhook_tokens.yml"
        if not token_file.exists():
            return None
        return WebhookTokensYamlFile.create_from_path(path=token_file).get_token(
            command_str
        )

    def _parse(self, command_path: str) -> tuple[str, str, str] | None:
        parts = command_path.split("/", 2)
        if len(parts) < 3:
            return None
        return parts[0], parts[1], parts[2]
