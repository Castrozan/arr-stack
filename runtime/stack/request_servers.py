from arr_config_provisioner.runtime_config import read_app_api_key
from stack.onboarding_http import JsonClient
from stack.provisioning import APPLICATION_URLS


def desired_server(app):
    api_key = read_app_api_key("/stack/config", app)
    client = JsonClient(APPLICATION_URLS[app], {"X-Api-Key": api_key})
    profile_name = "HD - Original Language" if app == "sonarr" else "HD - 720p/1080p"
    profiles = client.request("GET", "/api/v3/qualityprofile")
    profile = next(value for value in profiles if value["name"] == profile_name)
    server = {
        "name": app.title(),
        "hostname": app,
        "port": 8989 if app == "sonarr" else 7878,
        "apiKey": api_key,
        "useSsl": False,
        "baseUrl": "",
        "activeProfileId": profile["id"],
        "activeProfileName": profile_name,
        "activeDirectory": "/data/media/tv"
        if app == "sonarr"
        else "/data/media/movies",
        "tags": [],
        "is4k": False,
        "isDefault": True,
        "syncEnabled": True,
        "preventSearch": False,
        "tagRequests": False,
        "overrideRule": [],
    }
    if app == "sonarr":
        server.update(
            {
                "seriesType": "standard",
                "animeSeriesType": "anime",
                "enableSeasonFolders": True,
            }
        )
    else:
        server["minimumAvailability"] = "released"
    return server


def configure_request_servers(client):
    for app in ("radarr", "sonarr"):
        servers = client.request("GET", f"/api/v1/settings/{app}")
        existing = next(
            (
                server
                for server in servers
                if server["hostname"] == app and not server["is4k"]
            ),
            None,
        )
        desired = desired_server(app)
        if existing:
            writable = {key: value for key, value in existing.items() if key != "id"}
            client.request(
                "PUT",
                f"/api/v1/settings/{app}/{existing['id']}",
                {**writable, **desired},
            )
        else:
            client.request("POST", f"/api/v1/settings/{app}", desired)
