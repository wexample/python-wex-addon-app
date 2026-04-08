from __future__ import annotations

from pathlib import Path


def get_helper_app_path(name: str, env: str) -> Path:
    return Path(f"/var/www/{env}/wex-{name}")


def get_helper_docker_compose(name: str) -> str:
    return f"""\
services:
  {name}:
    image: nginxproxy/nginx-proxy:1.3
    container_name: ${{APP_PROJECT_NAME}}_{name}
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ${{APP_PATH}}{name}/certs:/etc/nginx/certs:ro
      - ${{APP_PATH}}{name}/logs:/var/log/nginx
      - ${{APP_PATH}}{name}/vhost.d:/etc/nginx/vhost.d
      - ${{APP_PATH}}{name}/html:/usr/share/nginx/html
      - ${{APP_PATH}}{name}/wex.conf:/etc/nginx/conf.d/wex.conf
    privileged: true
    extends:
      file: ${{SERVICE_DEFAULT_COMPOSE}}
      service: default
"""


def get_helper_wex_conf() -> str:
    return """\
# Allow big files transfer.
client_max_body_size 100M;

server {
    listen 80 default_server;
    server_name _;
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
}
"""
