from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.middleware import middleware

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@middleware(middleware=AppMiddleware)
@command(
    type=COMMAND_TYPE_ADDON,
    description="Run performance benchmarks and display a report. Python only (requires pytest-benchmark tests).",
)
def app__performance__report(context: ExecutionContext, app_workdir: AppMiddleware) -> None:
    from wexample_wex_addon_app.workdir.mixin.abstract_profiling_workdir_mixin import (
        AbstractProfilingWorkdirMixin,
    )

    if not isinstance(app_workdir, AbstractProfilingWorkdirMixin):
        context.io.warning(
            f"Performance profiling is not supported for workdir type: {type(app_workdir).__name__}"
        )
        return

    result = app_workdir.run_profiling()

    if "error" in result:
        context.io.error(result["error"])
        return

    entries = result.get("entries", [])

    if not entries:
        context.io.warning("No benchmark results found.")
        return

    context.io.properties(
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
