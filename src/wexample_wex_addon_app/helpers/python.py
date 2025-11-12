from __future__ import annotations

import shutil

from wexample_helpers.const.types import PathOrString


def python_install_environment(path: PathOrString) -> bool:
    from pathlib import Path

    from wexample_helpers.helpers.shell import shell_run

    project_path = Path(path)

    # This is a non installed app.
    if project_path.exists():
        venv_path = project_path / ".venv"
        lock_path = project_path / "pdm.lock"

        # Ensure we start from a clean environment
        if venv_path.exists():
            if venv_path.is_dir():
                shutil.rmtree(venv_path, ignore_errors=True)
            else:
                venv_path.unlink(missing_ok=True)
        if lock_path.exists():
            lock_path.unlink()

        # Recreate virtualenv the same way we do manually
        shell_run(
            cmd=["python3", "-m", "venv", ".venv", "--clear", "--copies"],
            cwd=project_path,
            inherit_stdio=True,
        )

        # Force PDM to use the local .venv
        shell_run(
            cmd=["pdm", "use", ".venv"],
            cwd=project_path,
            inherit_stdio=True,
        )

        # Install dependencies with a fresh resolution
        shell_run(
            cmd=["pdm", "install"],
            cwd=project_path,
            inherit_stdio=True,
        )

        return True
    return False
