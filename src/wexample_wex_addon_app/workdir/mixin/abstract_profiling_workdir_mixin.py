from __future__ import annotations

from abc import abstractmethod


class AbstractProfilingWorkdirMixin:
    """Abstract interface for workdirs that support performance profiling.

    Language-specific addons (e.g. wex-addon-dev-python) implement this by
    extending both this class and WithRunnerWorkdirMixin.

    ``report.py`` uses ``isinstance(workdir, AbstractProfilingWorkdirMixin)``
    to detect whether the current workdir supports profiling — no import of
    any language-specific addon is required.
    """

    def get_benchmark_dir(self) -> str:
        """Return the directory (relative to the workdir root) that contains benchmark tests."""
        return "benchmarks/"

    @abstractmethod
    def run_profiling(self) -> dict:
        """Run benchmarks and return a parsed result dict.

        Returns a dict with:
            - "language": str
            - "tool": str
            - "entries": list[dict]  (keys: name, min_ms, mean_ms, median_ms, max_ms, rounds)
        On failure:
            - "error": str
        """
