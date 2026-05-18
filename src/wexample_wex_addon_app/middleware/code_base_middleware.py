from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_wex_core.common.command_request import CommandRequest

    from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir


class CodeBaseMiddleware(AppMiddleware):
    def _create_app_workdir(
        self, request: CommandRequest, app_path: str
    ) -> CodeBaseWorkdir:
        from pathlib import Path

        from wexample_wex_addon_app.workdir.code_base_workdir import CodeBaseWorkdir

        return CodeBaseWorkdir.create_from_path(
            path=Path(app_path).resolve(),
            parent_io_handler=request.kernel,
        )
