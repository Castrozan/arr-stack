import base64
import hashlib
import json
import os
import secrets
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

APPLICATION_PORTS = {"sonarr": 8989, "radarr": 7878, "prowlarr": 9696}
CONFIGURATION_DIRECTORIES = (
    "qbittorrent",
    "sonarr",
    "radarr",
    "prowlarr",
    "bazarr",
    "jellyfin",
    "jellyseerr",
    "suwayomi",
    "miwayomi",
    "miwayomi-update-disabled",
    "flaresolverr",
    "audiobookshelf",
    "audiobookshelf-metadata",
    "readmeabook/config",
    "readmeabook/cache",
    "readmeabook/pgdata",
    "readmeabook/redis",
)
DATA_DIRECTORIES = (
    "torrents/incomplete",
    "torrents/audiobooks",
    "media/movies",
    "media/tv",
    "media/movies-private",
    "media/tv-private",
    "manga",
    "audiobooks",
)


def create_file(path, contents, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    except FileExistsError:
        return False
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        output.write(contents)
    return True


def credentials(state):
    path = state / "credentials.json"
    return json.loads(path.read_text())


def application_configuration(port):
    configuration = Element("Config")
    values = {
        "ApiKey": secrets.token_hex(16),
        "Port": str(port),
        "BindAddress": "*",
        "LaunchBrowser": "False",
        "AuthenticationMethod": "Forms",
        "AuthenticationRequired": "Enabled",
        "LogLevel": "info",
    }
    for name, value in values.items():
        SubElement(configuration, name).text = value
    return tostring(configuration, encoding="unicode") + "\n"


def torrent_configuration(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha512", password.encode(), salt, 100000)
    encoded = f"{base64.b64encode(salt).decode()}:{base64.b64encode(digest).decode()}"
    return (
        "[BitTorrent]\nSession\\DefaultSavePath=/data/torrents\n"
        "Session\\TempPath=/data/torrents/incomplete\nSession\\Port=6881\n"
        "[Preferences]\nWebUI\\Username=admin\n"
        f'WebUI\\Password_PBKDF2="@ByteArray({encoded})"\n'
        "WebUI\\ServerDomains=qbittorrent;localhost;127.0.0.1\n"
        "WebUI\\Address=*\nWebUI\\Port=8080\n"
    )


def initialize(
    config_root=Path("/stack/config"), data=Path("/data"), state=Path("/state")
):
    user = int(os.environ.get("PUID", "1000"))
    group = int(os.environ.get("PGID", "1000"))
    state.mkdir(parents=True, exist_ok=True)
    if not (state / "credentials.json").exists():
        existing = [config_root / app / "config.xml" for app in APPLICATION_PORTS]
        existing.append(config_root / "qbittorrent/qBittorrent/qBittorrent.conf")
        if any(path.exists() for path in existing):
            raise RuntimeError(
                "Restore the state volume before starting with existing application configuration"
            )
        generated = {
            app: secrets.token_urlsafe(24)
            for app in (*APPLICATION_PORTS, "qbittorrent", "bazarr", "jellyfin")
        }
        create_file(state / "credentials.json", json.dumps(generated, indent=2) + "\n")
    values = credentials(state)
    for directory in CONFIGURATION_DIRECTORIES:
        path = config_root / directory
        path.mkdir(parents=True, exist_ok=True)
        os.chown(
            path,
            1000 if directory == "jellyseerr" else user,
            1000 if directory == "jellyseerr" else group,
        )
    for directory in DATA_DIRECTORIES:
        path = data / directory
        path.mkdir(parents=True, exist_ok=True)
        for parent in (path, *path.parents):
            if parent == data.parent:
                break
            os.chown(parent, user, group)
            parent.chmod(0o775)
    for app, port in APPLICATION_PORTS.items():
        path = config_root / app / "config.xml"
        if create_file(path, application_configuration(port), 0o640):
            os.chown(path, user, group)
    path = config_root / "qbittorrent/qBittorrent/qBittorrent.conf"
    if create_file(path, torrent_configuration(values["qbittorrent"]), 0o640):
        os.chown(path.parent, user, group)
        os.chown(path, user, group)
    bazarr_configuration = {
        "auth": {
            "type": "form",
            "username": "admin",
            "password": hashlib.md5(values["bazarr"].encode()).hexdigest(),
        },
        "sonarr": {"ip": "sonarr", "port": 8989},
        "radarr": {"ip": "radarr", "port": 7878},
        "general": {"use_sonarr": True, "use_radarr": True},
    }
    for app in APPLICATION_PORTS:
        if app in bazarr_configuration:
            from xml.etree.ElementTree import parse

            bazarr_configuration[app]["apikey"] = parse(
                config_root / app / "config.xml"
            ).findtext("ApiKey")
    path = config_root / "bazarr/config/config.yaml"
    if create_file(path, json.dumps(bazarr_configuration, indent=2), 0o640):
        os.chown(path.parent, user, group)
        os.chown(path, user, group)
    print("Storage and credentials initialized; existing configuration preserved.")
