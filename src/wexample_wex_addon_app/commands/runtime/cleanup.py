from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_wex_core.const.globals import COMMAND_TYPE_ADDON
from wexample_wex_core.decorator.command import command

if TYPE_CHECKING:
    from wexample_wex_core.context.execution_context import ExecutionContext


@command(type=COMMAND_TYPE_ADDON)
def app__runtime__cleanup(context: ExecutionContext) -> None:
    from wexample_filestate_flutter.option.flutter.abstract_flutter_file_content_option import AbstractFlutterFileContentOption
    from wexample_filestate_javascript.option.javascript.abstract_javascript_file_content_option import AbstractJavascriptFileContentOption
    from wexample_filestate_php.option.php.abstract_php_file_content_option import AbstractPhpFileContentOption
    from wexample_helpers.helpers.docker import (
        docker_container_is_running,
        docker_image_exists,
        docker_remove_container,
        docker_remove_image,
        docker_stop_container,
    )
    from wexample_helpers.helpers.shell import shell_run

    known_images = {
        AbstractPhpFileContentOption.DOCKER_IMAGE_NAME,
        AbstractJavascriptFileContentOption.DOCKER_IMAGE_NAME,
        AbstractFlutterFileContentOption.DOCKER_IMAGE_NAME,
    }

    # Find containers using known images
    result = shell_run(
        cmd=["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Image}}"],
        capture=True,
    )
    containers_to_remove = [
        line.split("\t")[0]
        for line in result.stdout.strip().splitlines()
        if "\t" in line and line.split("\t")[1] in known_images
    ]

    removed_containers = 0
    for name in containers_to_remove:
        if docker_container_is_running(name):
            docker_stop_container(name)
        docker_remove_container(name)
        removed_containers += 1

    removed_images = 0
    for image_name in known_images:
        if docker_image_exists(image_name):
            docker_remove_image(image_name)
            removed_images += 1

    if removed_containers == 0 and removed_images == 0:
        context.io.success("Nothing to clean up.")
    else:
        context.io.success(
            f"Cleaned up {removed_containers} container(s) and {removed_images} image(s)."
        )
