from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING, Any

from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_prompt.enums.verbosity_level import VerbosityLevel
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="List app containers in a compact table",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.CONTAINER,
        DomainTag.DOCKER,
        EffectTag.READ_ONLY,
        EffectTag.SUBPROCESS_SPAWN,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.CONTAINER,
        ScopeTag.LOCAL,
    ],
)
def app__container__list(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
) -> AbstractResponse:
    from wexample_app.const.globals import WORKDIR_SETUP_DIR
    from wexample_app.response.default_response import DefaultResponse
    from wexample_app.response.table_response import TableResponse

    from wexample_wex_addon_app.item.file.docker_compose_yaml_file import (
        DockerComposeYamlFile,
    )

    compose_path = (
        app_workdir.get_path()
        / WORKDIR_SETUP_DIR
        / "tmp"
        / "docker-compose.runtime.yml"
    )
    if not compose_path.exists():
        return DefaultResponse(
            kernel=context.kernel,
            content="Runtime docker-compose file is missing",
        )

    services = DockerComposeYamlFile.create_from_path(path=compose_path).read_services()
    if not services:
        return DefaultResponse(
            kernel=context.kernel,
            content="No app containers declared in runtime docker-compose",
        )

    container_names = [
        attrs.get("container_name", service_name)
        for service_name, attrs in services.items()
    ]

    inspect_by_name: dict[str, dict[str, Any]] = {}
    result = subprocess.run(
        ["docker", "inspect", *container_names],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        for item in json.loads(result.stdout):
            inspect_by_name[item["Name"].lstrip("/")] = item

    verbose = context.io.default_context_verbosity >= VerbosityLevel.HIGH
    headers = ["Role", "Service", "State", "Ports"]
    if verbose:
        headers += ["Image", "Container"]

    main_service = app_workdir.get_main_service()
    main_db_service = app_workdir.get_main_db_service()

    rows: list[list[str]] = []
    for service_name, attrs in services.items():
        container_name = attrs.get("container_name", service_name)
        inspect = inspect_by_name.get(container_name, {})
        state = inspect.get("State", {})
        config = inspect.get("Config", {})

        row = [
            _format_role(service_name=service_name, main_service=main_service, main_db_service=main_db_service),
            service_name,
            _format_state(
                status=state.get("Status"),
                health=(state.get("Health") or {}).get("Status"),
            ),
            _format_ports((inspect.get("NetworkSettings") or {}).get("Ports")),
        ]
        if verbose:
            row += [
                config.get("Image") or attrs.get("image", "-"),
                container_name,
            ]
        rows.append(row)

    return TableResponse(
        kernel=context.kernel,
        content=rows,
        headers=headers,
    )


def _format_ports(port_bindings: dict[str, Any] | None) -> str:
    if not port_bindings:
        return "-"

    items: list[str] = []
    for container_port, bindings in sorted(port_bindings.items()):
        target = container_port.split("/", 1)[0]
        if not bindings:
            items.append(target)
            continue

        for binding in bindings:
            host_port = binding.get("HostPort")
            if host_port:
                items.append(f"{host_port}->{target}")

    return ", ".join(items) if items else "-"


def _format_role(service_name: str, main_service: str | None, main_db_service: str | None) -> str:
    if service_name == main_service:
        return "@cyan{main}"
    if service_name == main_db_service:
        return "@yellow{db}"
    return "-"


def _format_state(status: str | None, health: str | None) -> str:
    status = status or "missing"
    if status == "running":
        state = "@green{running}"
    elif status in {"created", "restarting"}:
        state = f"@yellow{{{status}}}"
    else:
        state = f"@red{{{status}}}"

    if health:
        if health == "healthy":
            state += " @green{healthy}"
        elif health == "starting":
            state += " @yellow{starting}"
        else:
            state += f" @red{{{health}}}"

    return state
