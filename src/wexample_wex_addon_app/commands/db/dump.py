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
    name="file_name",
    type=str,
    required=False,
    description="Output file name (without extension, defaults to env-name-datetime)",
)
@option(
    name="tag",
    type=str,
    required=False,
    description="Suffix tag appended to the generated file name",
)
@option(
    name="zip",
    type=bool,
    is_flag=True,
    required=False,
    description="Zip the dump file (default: True)",
)
@option(
    name="service",
    type=str,
    required=False,
    description="DB service name (defaults to docker.db.main)",
)
@middleware(middleware=AppMiddleware)
@command(type=COMMAND_TYPE_ADDON, description="Create a database dump")
def app__db__dump(
    context: ExecutionContext,
    app_workdir: ManagedWorkdir,
    file_name: str | None = None,
    tag: str | None = None,
    zip: bool = True,
    service: str | None = None,
) -> AbstractResponse | str | None:
    import zipfile as _zipfile
    from datetime import datetime

    from wexample_app.response.warning_response import WarningResponse

    service_name = service or app_workdir.get_main_db_service()
    if not service_name:
        return WarningResponse(
            kernel=context.kernel,
            message="No DB service configured (docker.db.main), skipping dump",
        )

    runtime = app_workdir.get_runtime_config()
    env = runtime.search("app.env").get_str_or_default("local")
    db_name = (
        runtime.search(f"service.{service_name}.name").get_str_or_none()
        or runtime.search("db.main").get_str_or_none()
        or runtime.search("app.name").get_str()
    )

    if not file_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{env}-{db_name}-{timestamp}"
        if tag:
            file_name += f"-{tag}"

    context.io.log(f"Exporting dump: {file_name}")

    request = context.kernel._get_command_request_class()(
        kernel=context.kernel,
        name=f"@{service_name}::db/dump",
        arguments={
            "app_path": str(app_workdir.get_path()),
            "file_name": file_name,
        },
    )
    response = context.kernel.execute_kernel_command(request)
    dump_path_str = response.content if hasattr(response, "content") else None

    if not dump_path_str:
        return None

    from pathlib import Path

    dump_path = Path(dump_path_str)

    if not dump_path.exists():
        raise RuntimeError(f"Dump file not found: {dump_path}")

    output_path = dump_path

    if zip:
        context.io.log("Creating zip file")
        zip_path = dump_path.with_suffix(".sql.zip")
        with _zipfile.ZipFile(zip_path, "w", _zipfile.ZIP_DEFLATED) as zf:
            zf.write(dump_path, dump_path.name)
        dump_path.unlink()
        output_path = zip_path

        zip_symlink = dump_path.parent / "db.latest.zip"
        if zip_symlink.is_symlink():
            zip_symlink.unlink()
        zip_symlink.symlink_to(zip_path.name)

    symlink = dump_path.parent / "db.latest"
    if symlink.is_symlink():
        symlink.unlink()
    symlink.symlink_to(output_path.name)

    return str(output_path)
