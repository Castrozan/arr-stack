import json
from pathlib import Path
from urllib.parse import urlencode

from stack.bootstrap import create_file, credentials
from stack.accounts import users
from stack.jellyfin_onboarding import onboard_jellyfin
from stack.onboarding_http import JsonClient
from stack.provisioning import configure
from stack.request_servers import configure_request_servers


def onboard():
    values = credentials(Path("/state"))
    configure()
    onboard_jellyfin(values["jellyfin"])
    users("sync")
    client = JsonClient("http://jellyseerr:5055")
    settings = json.loads(Path("/stack/config/jellyseerr/settings.json").read_text())
    login = {"username": "admin", "password": values["jellyfin"]}
    if not settings.get("jellyfin", {}).get("ip"):
        login.update(
            {
                "hostname": "jellyfin",
                "port": 8096,
                "useSsl": False,
                "urlBase": "",
                "serverType": 2,
            }
        )
    client.request("POST", "/api/v1/auth/jellyfin", login)
    libraries = client.request("GET", "/api/v1/settings/jellyfin/library?sync=true")
    public = [
        library["id"] for library in libraries if library["name"] in ("Movies", "TV")
    ]
    if len(public) != 2:
        raise RuntimeError(
            "Both public libraries must exist before enabling request-library sync"
        )
    client.request(
        "GET",
        "/api/v1/settings/jellyfin/library?" + urlencode({"enable": ",".join(public)}),
    )
    client.request(
        "POST",
        "/api/v1/settings/main",
        {
            "localLogin": False,
            "mediaServerLogin": True,
            "newPlexLogin": False,
            "defaultPermissions": 160,
            "applicationTitle": "arr-stack",
        },
    )
    configure_request_servers(client)
    client.request("POST", "/api/v1/settings/initialize")
    users("sync-account-permissions")
    users("sync-request-routing")
    create_file(Path("/state/onboarding-complete"), "complete\n")
    configure()
    print(
        "Jellyfin and Jellyseerr are ready. Friends use one account for watching and requesting."
    )
