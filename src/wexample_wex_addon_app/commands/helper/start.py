from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.as_sudo import as_sudo
from wexample_wex_core.decorator.command import command
from wexample_wex_core.decorator.option import option

if TYPE_CHECKING:
    from wexample_app.response.abstract_response import AbstractResponse
    from wexample_wex_core.context.execution_context import ExecutionContext

_PROXY_DOCKER_COMPOSE = """\
services:
  proxy:
    image: nginxproxy/nginx-proxy:1.3
    container_name: ${APP_PROJECT_NAME}_proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ${APP_PATH}proxy/certs:/etc/nginx/certs:ro
      - ${APP_PATH}proxy/logs:/var/log/nginx
      - ${APP_PATH}proxy/vhost.d:/etc/nginx/vhost.d
      - ${APP_PATH}proxy/html:/usr/share/nginx/html
      - ${APP_PATH}proxy/wex.conf:/etc/nginx/conf.d/wex.conf
    privileged: true
    extends:
      file: ${SERVICE_DEFAULT_COMPOSE}
      service: default
"""

_PROXY_WEX_CONF = """\
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


@option(
    name="env",
    type=str,
    required=False,
    description="Environment (defaults to local)",
)
@as_sudo()
@command(type=COMMAND_TYPE_ADDON, description="Create and start the proxy helper app")
def app__helper__start(
    context: ExecutionContext,
    env: str | None = None,
) -> AbstractResponse:
    import shutil
    from pathlib import Path

    from wexample_app.response.queued_collection_response import QueuedCollectionResponse

    env = env or "local"
    proxy_path = Path(f"/var/www/{env}/wex-proxy")

    def _create(previous_value=None) -> None:
        if proxy_path.exists():
            shutil.rmtree(proxy_path)

        # Directory structure
        for subdir in [
            ".wex/docker",
            ".wex/tmp",
            "proxy/certs",
            "proxy/html",
            "proxy/logs",
            "proxy/vhost.d",
        ]:
            (proxy_path / subdir).mkdir(parents=True)

        # .wex/config.yml
        (proxy_path / ".wex" / "config.yml").write_text(
            "global:\n"
            "  type: app\n"
            "  name: wex-proxy\n"
            "  main_service: proxy\n"
            "  version: 1.0.0\n"
            "service:\n"
            "  proxy: {}\n"
        )

        # .wex/.env
        (proxy_path / ".wex" / ".env").write_text(f"APP_ENV={env}\n")

        # .wex/docker/docker-compose.yml
        (proxy_path / ".wex" / "docker" / "docker-compose.yml").write_text(
            _PROXY_DOCKER_COMPOSE
        )

        # proxy/wex.conf
        (proxy_path / "proxy" / "wex.conf").write_text(_PROXY_WEX_CONF)

        context.io.log(f"Proxy app created at {proxy_path}")

    def _start(previous_value=None):
        from wexample_wex_addon_app.commands.app.start import app__app__start

        return context.kernel.run_function(app__app__start, {"app_path": str(proxy_path)})

    return QueuedCollectionResponse(kernel=context.kernel, content=[_create, _start])
