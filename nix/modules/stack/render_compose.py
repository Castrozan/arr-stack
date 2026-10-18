import json
import sys

import yaml


def configuration_path(volume):
    nested = {
        f"readmeabook-{name}": f"readmeabook/{name}"
        for name in ("config", "cache", "pgdata", "redis")
    }
    return "${ARR_CONFIG_ROOT}/" + nested.get(volume, volume)


def render_compose(document, settings):
    services = document["services"]
    for name in ("initialize", "configure", "manage", "cleanup"):
        services.pop(name)
    for name, service in services.items():
        service["container_name"] = f"arr-{name}"
        service.pop("profiles", None)
        service["restart"] = (
            "no"
            if name in ("qbittorrent", "sonarr", "radarr", "prowlarr", "bazarr")
            else "unless-stopped"
        )
        service.get("depends_on", {}).pop("initialize", None)
        if not service.get("depends_on"):
            service.pop("depends_on", None)
        if settings["containerCgroupParent"]:
            service["cgroup_parent"] = settings["containerCgroupParent"]
        mounts = []
        for mount in service.get("volumes", []):
            volume, destination = mount.split(":", 1)
            if volume == "data":
                if name == "jellyfin":
                    mounts.append("${ARR_DATA_ROOT}/media:/media:ro")
                elif name == "suwayomi":
                    mounts.append(
                        "${ARR_DATA_ROOT}/manga:/home/suwayomi/.local/share/Tachidesk/downloads"
                    )
                else:
                    mounts.append("${ARR_DATA_ROOT}:" + destination)
            elif volume.startswith("./"):
                mounts.append(
                    "${MIWAYOMI_GATEWAY_CONFIG_PATH}:/etc/nginx/conf.d/default.conf:ro"
                )
            else:
                mounts.append(configuration_path(volume) + ":" + destination)
        service["volumes"] = mounts
        environment = service.setdefault("environment", {})
        environment.pop("DOWNLOADS_PATH", None)
        if name in (
            "prowlarr",
            "jellyseerr",
            "suwayomi",
            "miwayomi",
            "flaresolverr",
            "audiobookshelf",
            "readmeabook",
        ):
            service["dns"] = ["1.1.1.1", "8.8.8.8"]
        if name == "qbittorrent":
            service["ports"] = [
                port for port in service["ports"] if not port.endswith(("/tcp", "/udp"))
            ]
        if (
            name in ("jellyfin", "jellyseerr")
            and settings["bindAddress"] != "127.0.0.1"
        ):
            port = "8096" if name == "jellyfin" else "5055"
            service["ports"].append(f"127.0.0.1:{port}:{port}")
    services["jellyseerr"]["build"]["context"] = "${JELLYSEERR_EMAIL_BUILD_CONTEXT}"
    services["jellyseerr"]["image"] = (
        "local/jellyseerr-email:${JELLYSEERR_EMAIL_IMAGE_VERSION}"
    )
    services["jellyseerr"]["pull_policy"] = "build"
    services["miwayomi"]["build"]["context"] = "${MIWAYOMI_BUILD_CONTEXT}"
    services["miwayomi"]["build"]["args"]["MIWAYOMI_WEB_CACHE_VERSION"] = (
        "${MIWAYOMI_WEB_CACHE_VERSION}"
    )
    services["miwayomi"]["image"] = "arr-miwayomi:0.2.9-watch-progress"
    if settings["hardwareAcceleration"] == "nvidia":
        services["jellyfin"]["devices"] = ["nvidia.com/gpu=all"]
        services["jellyfin"]["environment"].update(
            {"NVIDIA_VISIBLE_DEVICES": "all", "NVIDIA_DRIVER_CAPABILITIES": "all"}
        )
    document["name"] = "arr-stack"
    document["networks"] = {
        "arrnet": {
            "driver": "bridge",
            "ipam": {"config": [{"subnet": "172.28.0.0/16"}]},
        }
    }
    document.pop("volumes", None)
    return document


if __name__ == "__main__":
    with open(sys.argv[1]) as source, open(sys.argv[2]) as configuration:
        yaml.safe_dump(
            render_compose(yaml.safe_load(source), json.load(configuration)),
            sys.stdout,
            sort_keys=False,
        )
