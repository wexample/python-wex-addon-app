from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from wexample_app.const.globals import WORKDIR_SETUP_DIR

if TYPE_CHECKING:
    from wexample_runner.runner_config import RunnerConfig
    from wexample_runner.runner_result import RunnerResult


class WithRunnerWorkdirMixin:
    """Mixin that gives a workdir the ability to execute commands inside runners (e.g. Docker).

    Usage:
        1. Override `get_runners()` to declare named runners with their config.
        2. Call `runner_exec("runner_name", ["cmd", ...])` anywhere in the workdir.

    The runner is built and started automatically on first use.
    If ephemeral=True in the RunnerConfig, the container is destroyed after each call.
    """

    _runner_instances: dict[str, DockerRunner] = {}

    def get_runners(self) -> dict[str, RunnerConfig]:
        """Declare the runners available for this workdir.

        Override in subclasses to register named runners:

            def get_runners(self):
                return {
                    "roave": RunnerConfig(
                        dockerfile=str(WORKDIR_SETUP_DIR / "docker" / "Dockerfile.roave"),
                        mount_path=self.get_suite_path(),
                        container_workdir="/var/www/html",
                        ephemeral=False,
                    )
                }
        """
        return {}

    def runner_exec(
        self,
        runner_name: str,
        cmd: list[str] | str,
        workdir: str | None = None,
        env: dict[str, str] | None = None,
    ) -> RunnerResult:
        """Execute a command inside the named runner.

        Builds the image and starts the container automatically if needed.
        Destroys the container after execution if ephemeral=True.
        """
        runner = self._get_or_create_runner(runner_name)
        runner.ensure_running()

        result = runner.execute(cmd=cmd, workdir=workdir, env=env)

        if runner.ephemeral:
            runner.destroy()
            self._runner_instances.pop(runner_name, None)

        return result

    def _build_runner(self, runner_name: str) -> DockerRunner:
        from wexample_runner.runner.docker_runner import DockerRunner

        runners = self.get_runners()
        if runner_name not in runners:
            raise KeyError(
                f"Runner '{runner_name}' is not declared in {self.__class__.__name__}.get_runners()."
            )

        config = runners[runner_name]
        workdir_path = Path(self.get_path())

        # Resolve dockerfile: absolute path used as-is, relative resolved from workdir root
        dockerfile = Path(config.dockerfile)
        dockerfile_path = (
            dockerfile if dockerfile.is_absolute() else workdir_path / dockerfile
        )

        # image_name defaults to "wex-{runner_name}"
        image_name = config.image_name or f"wex-{runner_name}"

        # mount_path defaults to workdir's own path
        mount_path = Path(config.mount_path) if config.mount_path else workdir_path

        volumes = {str(mount_path): config.container_workdir, **config.volumes}

        return DockerRunner(
            image_name=image_name,
            dockerfile_path=dockerfile_path,
            volumes=volumes,
            workdir=config.container_workdir,
            ephemeral=config.ephemeral,
        )

    def _get_or_create_runner(self, runner_name: str) -> DockerRunner:
        pass

        if runner_name not in self._runner_instances:
            self._runner_instances[runner_name] = self._build_runner(runner_name)

        return self._runner_instances[runner_name]
