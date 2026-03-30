from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_addon_app.workdir.app_workdir import AppWorkdir

if TYPE_CHECKING:
    pass

class RunnableAppWorkdir(AppWorkdir):
    def start(self) -> None:
        """Start the application."""
        self.log("Starting application...")
        # Implementation will use docker-compose or similar

    def stop(self) -> None:
        """Stop the application."""
        self.log("Stopping application...")

    def restart(self) -> None:
        """Restart the application."""
        self.stop()
        self.start()

    def exec(self, command: str | list[str]) -> None:
        """Execute a command in the running application."""
        self.log(f"Executing command: {command}")

    def logs(self) -> None:
        """Show application logs."""
        self.log("Showing logs...")
