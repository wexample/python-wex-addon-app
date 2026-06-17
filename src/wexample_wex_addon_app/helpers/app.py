from __future__ import annotations

import os
import platform
import shutil
import socket
import stat
import subprocess
from pathlib import Path

from wexample_helpers.helpers.shell import shell_run

_DEFAULT_LOCAL_IP = "127.0.1.1"
_RUN_USER = Path("/run/user")
_SSH_SOCKET_CANDIDATES = (
    Path("keyring") / "ssh",
    Path("gnupg") / "S.gpg-agent.ssh",
)


def detect_ssh_socket() -> str | None:
    if not _RUN_USER.exists():
        return None
    for uid_dir in _RUN_USER.iterdir():
        for suffix in _SSH_SOCKET_CANDIDATES:
            candidate = uid_dir / suffix
            try:
                if stat.S_ISSOCK(os.stat(candidate).st_mode):
                    return str(candidate)
            except OSError:
                pass
    return None


def get_docker_local_ip() -> str:
    # Call platform.system() at runtime, not as a module-level constant:
    # the stdlib already caches the underlying uname, and a frozen constant
    # would make the platform branch impossible to override (in tests, or if
    # the value is ever monkeypatched).
    if platform.system() == "Darwin":
        return "127.0.0.1"

    if shutil.which("docker-machine"):
        try:
            result = shell_run(["docker-machine", "ip"])
            ip = (result.stdout or "").strip()
            if ip:
                return ip
        except subprocess.CalledProcessError:
            pass

    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return _DEFAULT_LOCAL_IP


def get_sidecar_path(name: str, env: str) -> Path:
    return Path(f"/var/www/{env}/wex-{name}")
