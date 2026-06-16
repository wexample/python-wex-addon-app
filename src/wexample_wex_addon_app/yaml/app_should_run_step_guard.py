from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.yaml.abstract_step_guard import AbstractStepGuard

if TYPE_CHECKING:
    from wexample_wex_core.common.kernel import Kernel


class AppShouldRunStepGuard(AbstractStepGuard):
    """Skip a step when ``app_should_run: true`` and the app is not started."""

    _STEP_OPTIONS: list[str] = ["app_should_run"]

    @classmethod
    def get_step_options(cls) -> list[str]:
        return cls._STEP_OPTIONS

    @staticmethod
    def _is_app_started(kernel: Kernel) -> bool:
        try:
            from wexample_app.const.output import OUTPUT_TARGET_NONE
            from wexample_wex_core.common.command_request import CommandRequest

            sub_request = CommandRequest(
                kernel=kernel,
                name="app::app/started",
                arguments={},
                output_target=[OUTPUT_TARGET_NONE],
            )
            result = kernel.execute_kernel_command(sub_request)
            return bool(result.content) if result is not None else False
        except Exception:
            return False

    def should_skip(self, step: dict, kernel: Kernel) -> bool:
        if not step.get("app_should_run"):
            return False
        return not self._is_app_started(kernel)
