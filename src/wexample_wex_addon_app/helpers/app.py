from __future__ import annotations

import platform
import shutil
import socket
import subprocess
from pathlib import Path

from wexample_helpers.helpers.shell import shell_run

_DEFAULT_LOCAL_IP = "127.0.1.1"


def detect_ssh_socket() -> str | None:
    import os
    import stat

    run_user = Path("/run/user")
    if not run_user.exists():
        return None
    for uid_dir in run_user.iterdir():
        for candidate in [
            str(uid_dir / "keyring" / "ssh"),
            str(uid_dir / "gnupg" / "S.gpg-agent.ssh"),
        ]:
            try:
                if stat.S_ISSOCK(os.stat(candidate).st_mode):
                    return candidate
            except OSError:
                pass
    return None


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
