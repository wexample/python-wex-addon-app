from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    "command_name",
    type=str,
    required=False,
    default=None,
    description=(
        "Command to secure. Accepts any of the three webhook command shapes: "
        "'.ping/pong' (app-local), 'app::release/deploy' (addon), "
        "or '@nginx::status' (service)."
    ),
)
@option(
    "all",
    type=bool,
    is_flag=True,
    required=False,
    default=False,
    description=(
        "Generate tokens for all @webhook app-local commands in this app. "
        "Use 'wex core::webhook/token-generate --all --type-name addon|service' "
        "for the other types."
    ),
)
@option(
    "force",
    type=bool,
    is_flag=True,
    required=False,
    default=False,
    description="Revoke existing token and generate a new one",
)
@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Generate and store a webhook token (app, addon or service command)",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.HTTP,
        DomainTag.WEBHOOK,
        EffectTag.WRITE,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__webhook__token_generate(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    command_name: str | None = None,
    all: bool = False,
    force: bool = False,
):
    from wexample_app.response.failure_response import FailureResponse

    if not command_name and not all:
        return FailureResponse(
            kernel=context.kernel,
            message="Specify --command-name <cmd> or --all.",
        )
    if command_name and all:
        return FailureResponse(
            kernel=context.kernel,
            message="--command-name and --all are mutually exclusive.",
        )

    if all:
        webhook_cmds = (
            context.kernel.get_configuration_registry().get_webhook_commands()
        )
        targets = [
            cmd["command"]
            for cmd in webhook_cmds.values()
            if cmd["command"].startswith(".")
        ]
        if not targets:
            return "No @webhook app commands found."
    else:
        targets = [command_name]

    for cmd in targets:
        target = _resolve_target(context, app_workdir, cmd)
        if target is None:
            context.io.error(
                f"Unknown command shape: {cmd!r}. "
                "Expected '.group/name' (app), '<addon>::group/name' (addon) "
                "or '@svc::group/name' (service)."
            )
            continue
        target_workdir, namespace = target
        _generate_one(context, target_workdir, namespace, cmd, force)


def _generate_one(
    context, workdir, namespace: str, command_name: str, force: bool
) -> None:
    existing = workdir.get_local_data_value(namespace, command_name)
    if existing:
        if not force:
            context.io.warning(
                f"Token already exists for {command_name} — skipping (use --force)."
            )
            return
        workdir.delete_local_data_value(namespace, command_name)

    token = workdir.rotate_local_token(namespace, command_name)
    context.io.log(f"Token generated for {command_name}:  @yellow{{{token}}}")


def _resolve_target(context, app_workdir, command_name: str):
    """Route the command to the right (workdir, namespace) pair.

    - '.foo/bar'         → app_workdir   / webhook_tokens
    - '<addon>::foo/bar' → kernel.workdir / webhook_tokens_addon
    - '@svc::foo/bar'    → kernel.workdir / webhook_tokens_service
    Returns None on unrecognised shapes (caller logs a user-facing error).
    """
    if command_name.startswith("."):
        return app_workdir, "webhook_tokens"
    if command_name.startswith("@"):
        return context.kernel.workdir, "webhook_tokens_service"
    if "::" in command_name:
        return context.kernel.workdir, "webhook_tokens_addon"
    return None
