from __future__ import annotations

import shutil
from pathlib import Path

from wexample_helpers.const.types import PathOrString
from wexample_helpers.helpers.shell import shell_run


def python_ensure_pip_or_fail(venv_path: Path) -> bool:
    # Ensure pip is installed in the venv
    shell_run(
        cmd=[
            f"{venv_path}/bin/python",
            "-m",
            "ensurepip",
            "--upgrade",
        ],
        cwd=venv_path.parent,
        inherit_stdio=True,
    )

    return True


def python_install_dependencies_in_venv(
    venv_path: Path, names: list[PathOrString], editable: bool = False
) -> None:
    for dependency_name in names:
        python_install_dependency_in_venv(
            venv_path=venv_path, name=dependency_name, editable=editable
        )


def python_install_dependency_in_venv(
    venv_path: Path, name: PathOrString, editable: bool = False
) -> None:
    from wexample_helpers.helpers.shell import shell_run

    cmd = [
        f"{venv_path}/bin/python",
        "-m",
        "pip",
        "install",
    ]

    if editable:
        cmd.append("-e")

    cmd.append(str(name))

    shell_run(
        cmd=cmd,
        cwd=venv_path.parent,
        inherit_stdio=True,
    )


def python_install_environment(path: PathOrString) -> Path:
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
            cmd=[
                str(python_bin),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
                "setuptools",
                "wheel",
            ],
            cwd=project_path,
            inherit_stdio=True,
        )

        shell_run(
            cmd=[str(python_bin), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=project_path,
            inherit_stdio=True,
        )

    return venv_path


def python_is_package_installed_editable_in_venv(
    venv_path: Path,
    package_name: str,
    package_path,
) -> bool:
    """Return True if the package is installed in editable mode at the given path."""
    import subprocess
    from pathlib import Path

    python_bin = venv_path / "bin" / "python"

    try:
        result = subprocess.run(
            [str(python_bin), "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return False

        editable_location = None

        for line in result.stdout.splitlines():
            if line.startswith("Editable project location:"):
                editable_location = line.split(":", 1)[1].strip()
                break

        if not editable_location:
            return False

        return Path(editable_location).resolve() == Path(package_path).resolve()

    except (subprocess.SubprocessError, OSError):
        return False
