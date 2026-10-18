import json
import os
from pathlib import Path

from arr_config_provisioner.qbittorrent_api_client import (
    build_authenticated_opener,
    read_preferences,
)
from arr_config_provisioner.runtime_config import read_app_api_key
from stack.onboarding_http import JsonClient
from stack.provisioning import APPLICATION_URLS


def application(app):
    return JsonClient(
        APPLICATION_URLS[app], {"X-Api-Key": read_app_api_key("/stack/config", app)}
    )


def verify_configuration():
    for app in ("radarr", "sonarr"):
        client = application(app)
        clients = client.request("GET", "/api/v3/downloadclient")
        assert len([value for value in clients if value["name"] == "qBittorrent"]) == 1
        assert (
            next(
                field["value"]
                for field in clients[0]["fields"]
                if field["name"] == "host"
            )
            == "qbittorrent"
        )
        roots = client.request("GET", "/api/v3/rootfolder")
        assert len(roots) == 2
        assert all(value["path"].startswith("/data/media/") for value in roots)
        names = [
            value["name"] for value in client.request("GET", "/api/v3/qualityprofile")
        ]
        assert len(names) == len(set(names))
        assert {"PT-BR Dublado", "PT-BR Legendado"} <= set(names)
        notifications = client.request("GET", "/api/v3/notification")
        assert (
            len(
                [
                    value
                    for value in notifications
                    if value["name"] == "Download cleanup"
                ]
            )
            == 1
        )
    prowlarr = application("prowlarr")
    applications = prowlarr.request("GET", "/api/v1/applications")
    assert sorted(value["name"] for value in applications) == ["Radarr", "Sonarr"]
    indexers = prowlarr.request("GET", "/api/v1/indexer")
    assert len(indexers) == 6
    values = json.loads(Path("/state/credentials.json").read_text())
    opener = build_authenticated_opener(
        APPLICATION_URLS["qbittorrent"], "admin", values["qbittorrent"]
    )
    preferences = read_preferences(opener, APPLICATION_URLS["qbittorrent"])
    assert preferences["save_path"].rstrip("/") == "/data/torrents"
    assert preferences["max_active_downloads"] == 3
    assert not preferences["max_ratio_enabled"]


def verify_storage():
    source = Path("/data/torrents/acceptance.tmp")
    destination = Path("/data/media/movies/acceptance.tmp")
    try:
        source.write_bytes(b"hardlink acceptance")
        os.link(source, destination)
        assert source.stat().st_ino == destination.stat().st_ino
        assert source.stat().st_nlink == 2
    finally:
        destination.unlink(missing_ok=True)
        source.unlink(missing_ok=True)


def verify_accounts():
    token = Path("/state/jellyfin-api-key").read_text().strip()
    jellyfin = JsonClient("http://jellyfin:8096", {"X-Emby-Token": token})
    libraries = jellyfin.request("GET", "/Library/VirtualFolders")
    public_ids = {
        value["ItemId"] for value in libraries if value["Name"] in ("Movies", "TV")
    }
    assert len(libraries) == 4
    accounts = jellyfin.request("GET", "/Users")
    friend = next(
        (value for value in accounts if value["Name"] == "acceptance-friend"), None
    )
    if friend:
        assert not friend["Policy"]["EnableAllFolders"]
        assert set(friend["Policy"]["EnabledFolders"]) == public_ids
        assert not friend["Policy"]["IsAdministrator"]
    settings = json.loads(Path("/stack/config/jellyseerr/settings.json").read_text())
    requester = JsonClient(
        "http://jellyseerr:5055", {"X-Api-Key": settings["main"]["apiKey"]}
    )
    assert settings["public"]["initialized"]
    assert not settings["main"]["localLogin"]
    enabled = {
        value["name"] for value in settings["jellyfin"]["libraries"] if value["enabled"]
    }
    assert enabled == {"Movies", "TV"}
    for app in ("sonarr", "radarr"):
        servers = requester.request("GET", f"/api/v1/settings/{app}")
        assert len(servers) == 1
        assert servers[0]["syncEnabled"]
    if friend:
        users = requester.request("GET", "/api/v1/user?take=200")["results"]
        account = next(
            value
            for value in users
            if value.get("jellyfinUsername") == "acceptance-friend"
        )
        assert account["permissions"] == 160


verify_configuration()
verify_storage()
verify_accounts()
print(
    "Application wiring, defaults, persistent storage, hardlinks, onboarding and account privacy verified."
)
