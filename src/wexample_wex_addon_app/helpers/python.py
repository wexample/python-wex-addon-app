from wexample_helpers.const.types import PathOrString


def python_install_environment(path: PathOrString) -> bool:
    from wexample_helpers.helpers.shell import shell_run

    # This is a non installed app.
    if path.exists():
        # Ensure .venv exists
        venv_path = path / ".venv"
        if not venv_path.exists():
            shell_run(
                cmd=["pdm", "venv", "create"],
                cwd=path,
                inherit_stdio=True,
            )

        # Force PDM to use the local .venv
        shell_run(
            cmd=["pdm", "use", ".venv"],
            cwd=path,
            inherit_stdio=True,
        )

        # Install dependencies
        shell_run(
            cmd=["pdm", "install"],
            cwd=path,
            inherit_stdio=True,
        )

        return True
    return False
