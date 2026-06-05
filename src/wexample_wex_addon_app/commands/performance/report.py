from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.const.tags import AudienceTag, EffectTag, ScopeTag
from wexample_wex_addon_app.const.tags import DomainTag
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_cli.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Run performance benchmarks and display a report. Python only (requires pytest-benchmark tests).",
    tags=[
        DomainTag.APP_LIFECYCLE,
        DomainTag.PERFORMANCE,
        EffectTag.READ_ONLY,
        AudienceTag.AGENT_SAFE,
        ScopeTag.APP,
        ScopeTag.LOCAL,
    ],
)
def app__performance__report(context: ExecutionContext, app_workdir: AppMiddleware):
    from wexample_app.response.failure_response import FailureResponse
    from wexample_app.response.properties_response import PropertiesResponse
    from wexample_app.response.warning_response import WarningResponse

    from wexample_wex_addon_app.workdir.mixin.abstract_profiling_workdir_mixin import (
        AbstractProfilingWorkdirMixin,
    )

    if not isinstance(app_workdir, AbstractProfilingWorkdirMixin):
        return WarningResponse(
            kernel=context.kernel,
            message=(
                f"Performance profiling is not supported for workdir type: "
                f"{type(app_workdir).__name__}"
            ),
        )

    result = app_workdir.run_profiling()

    if "error" in result:
        return FailureResponse(kernel=context.kernel, message=result["error"])

    entries = result.get("entries", [])

    if not entries:
        return WarningResponse(
            kernel=context.kernel, message="No benchmark results found."
        )

    return PropertiesResponse(
        kernel=context.kernel,
        title=f"Performance Report ({result['language']} / {result['tool']})",
        properties={
            entry["name"]: (
                f"median={entry['median_ms']}ms  "
                f"mean={entry['mean_ms']}ms  "
                f"min={entry['min_ms']}ms  "
                f"max={entry['max_ms']}ms  "
                f"({entry['rounds']} rounds)"
            )
            for entry in entries
        },
    )
