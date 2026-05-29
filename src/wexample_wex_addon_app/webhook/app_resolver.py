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

    def resolve_cwd(
        self,
        command_path: str,
        query_params: dict[str, list[str]] | None = None,
    ) -> str | None:
        parsed = self._parse(command_path)
        if parsed is None:
            return None
        env, app_name, _ = parsed
        return str(self._base / env / app_name)

    def resolve_token(self, command_path: str, command_str: str) -> str | None:
        import yaml
        from wexample_app.const.globals import WORKDIR_LOCAL_DIR_NAME, WORKDIR_SETUP_DIR

        cwd = self.resolve_cwd(command_path)
        if not cwd:
            return None
        token_file = (
            Path(cwd)
            / WORKDIR_SETUP_DIR
            / WORKDIR_LOCAL_DIR_NAME
            / "webhook_tokens.yml"
        )
        if not token_file.exists():
            return None
        try:
            with open(token_file) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return None
        return data.get(command_str)

    def _parse(self, command_path: str) -> tuple[str, str, str] | None:
        parts = command_path.split("/", 2)
        if len(parts) < 3:
            return None
        return parts[0], parts[1], parts[2]
