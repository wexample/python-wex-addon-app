from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware
from wexample_wex_core.decorator.option import option

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    "command_name",
    type=str,
    required=True,
    description="App command to secure, e.g. '.ping/pong'",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Generate and store a webhook token for an app command")
def app__webhook__token_generate(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    command_name: str,
) -> None:
    import secrets

    import yaml

    app_path = app_workdir.get_path()
    token_file = app_path / ".wex" / "local" / "webhook_tokens.yml"
    token_file.parent.mkdir(parents=True, exist_ok=True)

    tokens: dict = {}
    if token_file.exists():
        with open(token_file) as f:
            tokens = yaml.safe_load(f) or {}

    if command_name in tokens:
        context.io.warning(f"A token already exists for {command_name}. Use token-revoke first.")
        return

    token = secrets.token_hex(32)
    tokens[command_name] = token

    with open(token_file, "w") as f:
        yaml.dump(tokens, f, default_flow_style=False, sort_keys=True)

    context.io.log(f"Token generated for {command_name}:")
    context.io.log(f"  @yellow{{{token}}}")
    context.io.log("Store it now — it will not be shown again.")
