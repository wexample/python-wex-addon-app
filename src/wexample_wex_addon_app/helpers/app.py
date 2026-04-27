from __future__ import annotations

import platform
import shutil
import socket
import subprocess
from pathlib import Path

from wexample_helpers.helpers.shell import shell_run

_DEFAULT_LOCAL_IP = "127.0.1.1"


def get_docker_local_ip() -> str:
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
