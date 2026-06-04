from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_cli.decorator.command import command
from wexample_cli.decorator.middleware import middleware
from wexample_cli.decorator.option import option
from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON

from wexample_wex_addon_app.middleware.app_middleware import AppMiddleware

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_cli.context.execution_context import ExecutionContext

    from wexample_wex_addon_app.workdir.managed_workdir import ManagedWorkdir


@option(
    name="file_path",
    type=str,
    required=False,
    description="Path or filename of the dump to restore (prompted if omitted)",
)
@option(
    name="database",
    type=str,
    required=False,
    description="Database name (overrides db.main from runtime config)",
)
@option(
    name="service",
    type=str,
    required=False,
    description="DB service name (defaults to docker.db.main)",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Restore a database from a dump")
def app__db__restore(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    file_path: str | None = None,
    database: str | None = None,
    service: str | None = None,
) -> AbstractResponse | None:
    import zipfile
    from pathlib import Path

    from wexample_app.const.globals import WORKDIR_SETUP_DIR
    from wexample_app.response.success_response import SuccessResponse

    service_name = service or app_workdir.get_main_db_service()
    if not service_name:
        raise RuntimeError("No DB service configured (docker.db.main)")

    dumps_dir = app_workdir.get_path() / WORKDIR_SETUP_DIR / service_name / "dumps"
    dumps_dir.mkdir(parents=True, exist_ok=True)

    # Build list of available dumps (zip + sql, excluding symlinks)
    all_dumps = sorted(
        p
        for pattern in ("*.zip", "*.sql")
        for p in dumps_dir.glob(pattern)
        if not p.is_symlink()
    )

    if not all_dumps:
        raise RuntimeError(f"No dumps found in {dumps_dir}")

    dump_map = {p.name: p for p in all_dumps}

    # Resolve file_path
    if file_path:
        resolved = Path(file_path)
        if not resolved.is_absolute():
            resolved = dump_map.get(file_path) or dumps_dir / file_path
    else:
        response = context.io.choice(
            question="Please select a dump to restore",
            choices=list(dump_map.keys()),
            abort="Abort",
        )
        chosen = response.get_answer()
        if not chosen:
            return None
        resolved = dump_map[chosen]

    resolved = Path(resolved)
    if not resolved.exists():
        raise RuntimeError(f"Dump file not found: {resolved}")

    is_zip = resolved.suffix == ".zip"
    sql_path = resolved

    if is_zip:
        context.io.log("Unpacking...")
        with zipfile.ZipFile(resolved, "r") as zf:
            names = zf.namelist()
            if not names:
                raise RuntimeError("Zip file is empty")
            zf.extractall(dumps_dir)
            sql_path = dumps_dir / names[0]
        context.io.log(f"Extracted: {sql_path.name}")

    app_path = str(app_workdir.get_path())

    extra = {"database": database} if database else {}

    # Destroy + recreate DB
    context.io.log("Restoring...")
    context.kernel.execute_kernel_command(
        context.kernel._get_command_request_class()(
            kernel=context.kernel,
            name=f"@{service_name}::db/destroy",
            arguments={"app_path": app_path, **extra},
        )
    )

    # Restore from SQL file
    context.kernel.execute_kernel_command(
        context.kernel._get_command_request_class()(
            kernel=context.kernel,
            name=f"@{service_name}::db/restore",
            arguments={"app_path": app_path, "file_name": sql_path.name, **extra},
        )
    )

    # Clean up extracted SQL if it came from a zip
    if is_zip and sql_path.exists():
        sql_path.unlink()

    return SuccessResponse(
        kernel=context.kernel,
        message="Restoration complete",
    )
