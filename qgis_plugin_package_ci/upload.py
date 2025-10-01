#
# Upload plugin to osgeo
#
import base64
import re
import xmlrpc.client

from pathlib import Path

from . import logger
from .errors import PluginPackageError
from .parameters import Parameters


def upload_plugin(
    parameters: Parameters,
    *,
    username: str,
    password: str,
    archive: Path,
    dry_run: bool = False,
):
    server_url = str(parameters.upload_url)

    encoded_auth_string = base64.b64encode(f"{username}:{password}".encode()).decode("utf-8")
    server = xmlrpc.client.ServerProxy(
        server_url,
        verbose=logger.is_enabled_for(logger.LogLevel.DEBUG),
        headers=[("Authorization", f"Basic {encoded_auth_string}")],
    )

    if dry_run:
        with archive.open("rb") as _:  # Test that archive is ok
            logger.notice(f"Not uploading {archive} to {server_url} because it is a dry run.")
            return

    try:
        logger.debug("Uploading '%s' to QGIS plugins repository: %s", archive, server_url)
        with archive.open("rb") as fh:
            plugin_id, version_id = server.plugin.upload(  # type: ignore [misc]
                xmlrpc.client.Binary(fh.read()),
            )
            logger.debug("Plugin ID: %r -- Version ID: %r", plugin_id, version_id)
    except xmlrpc.client.ProtocolError as err:
        url = re.sub(r":[^/].*@", ":******@", err.url)
        logger.error(
            "=== A protocol error occurred ===\n"
            f"URL: {url}\n"
            f"HTTP/HTTPS headers: {err.headers}\n"
            f"Error code: {err.errcode}\n"
            f"Error message: {err.errmsg}\n"
            f"Plugin path: {archive}"
        )
        raise PluginPackageError(f"Failed to upload plugin '{archive}' on {server_url}") from None
    except xmlrpc.client.Fault as err:
        logger.error(
            "=== A fault occurred occurred ===\n"
            f"Fault code: {err.faultCode}\n"
            f"Fault string: {err.faultString}\n"
            f"Plugin path: {archive}"
        )
        raise PluginPackageError(f"Failed to upload plugin '{archive}' on {server_url}") from None
