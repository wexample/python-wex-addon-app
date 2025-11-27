from __future__ import annotations

import shutil
from pathlib import Path
from wexample_helpers.const.types import PathOrString
from wexample_helpers.helpers.shell import shell_run


def python_install_environment(path: PathOrString) -> bool:
    project_path = Path(path)

    venv_path = project_path / ".venv"
    req_path = project_path / "requirements.txt"

    if venv_path.exists():
        shutil.rmtree(venv_path, ignore_errors=True)

    # Crée un nouveau venv
    shell_run(
        cmd=["python3", "-m", "venv", ".venv", "--clear", "--copies"],
        cwd=project_path,
        inherit_stdio=True,
    )

    if req_path.exists():
        python_bin = venv_path / "bin" / "python"

        shell_run(
            cmd=[str(python_bin), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            cwd=project_path,
            inherit_stdio=True,
        )

        shell_run(
            cmd=[str(python_bin), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=project_path,
            inherit_stdio=True,
        )

    return True
