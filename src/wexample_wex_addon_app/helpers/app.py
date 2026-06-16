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
_PLATFORM_SYSTEM = platform.system()
_SSH_SOCKET_CANDIDATES = (
    Path("keyring") / "ssh",
    Path("gnupg") / "S.gpg-agent.ssh",
)


def detect_ssh_socket() -> str | None:
    run_user = Path("/run/user")
    if not run_user.exists():
        return None
    for uid_dir in run_user.iterdir():
        for suffix in _SSH_SOCKET_CANDIDATES:
            candidate = uid_dir / suffix
            try:
                if stat.S_ISSOCK(os.stat(candidate).st_mode):
                    return str(candidate)
            except OSError:
                pass
    return None


def get_docker_local_ip() -> str:
    if _PLATFORM_SYSTEM == "Darwin":
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
