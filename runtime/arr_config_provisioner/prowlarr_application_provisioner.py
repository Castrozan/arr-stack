from urllib.parse import urlsplit

from arr_api_client import get_resource_list, request_json
from provisioner_logging import log


def remove_retired_applications(base_url, api_key, desired_applications, dry_run):
    desired_names = {application["name"] for application in desired_applications}
    removed = []
    for application in get_resource_list(base_url, api_key, "applications"):
        implementation = application.get("implementation", "")
        if implementation not in {"Lidarr", "Readarr"}:
            continue
        if application.get("name") in desired_names:
            continue
        upstream = next(
            (
                field.get("value", "")
                for field in application.get("fields", [])
                if field.get("name") == "baseUrl"
            ),
            "",
        )
        if urlsplit(upstream).hostname != implementation.lower():
            continue
        if not dry_run:
            request_json(
                "DELETE", f"{base_url}/applications/{application['id']}", api_key
            )
        removed.append(application["name"])
        log(
            f"{'[dry-run] ' if dry_run else ''}retired application: {application['name']}"
        )
    return removed
