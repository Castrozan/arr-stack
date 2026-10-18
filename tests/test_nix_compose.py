import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPECIFICATION = importlib.util.spec_from_file_location(
    "render_compose", ROOT / "nix/modules/stack/render_compose.py"
)
RENDERER = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(RENDERER)


def render(**overrides):
    settings = {
        "bindAddress": "192.0.2.10",
        "containerCgroupParent": None,
        "hardwareAcceleration": "cpu",
        **overrides,
    }
    return RENDERER.render_compose(
        yaml.safe_load((ROOT / "compose.yaml").read_text()), settings
    )


def test_nix_deployment_uses_existing_configuration_without_bootstrapping_credentials():
    document = render()
    services = document["services"]
    assert not {"initialize", "configure", "manage", "cleanup"}.intersection(services)
    for name, service in services.items():
        assert service["container_name"] == f"arr-{name}"
        assert "initialize" not in service.get("depends_on", {})
        assert "profiles" not in service
        assert all(
            mount.startswith(("${ARR_", "${MIWAYOMI_GATEWAY_CONFIG_PATH}"))
            for mount in service["volumes"]
        )
    assert services["jellyfin"]["volumes"] == [
        "${ARR_CONFIG_ROOT}/jellyfin:/config",
        "${ARR_DATA_ROOT}/media:/media:ro",
    ]
    assert document["networks"]["arrnet"]["ipam"]["config"] == [
        {"subnet": "172.28.0.0/16"}
    ]


def test_nix_supervisor_owns_the_download_chain_lifecycle():
    services = render()["services"]
    for name in ("sonarr", "radarr", "prowlarr", "bazarr", "qbittorrent"):
        assert services[name]["restart"] == "no"
    assert services["jellyfin"]["restart"] == "unless-stopped"
    assert len(services["qbittorrent"]["ports"]) == 1


def test_nix_gpu_and_cgroup_access_are_explicit():
    services = render()["services"]
    assert all("cgroup_parent" not in value for value in services.values())
    assert "devices" not in services["jellyfin"]
    services = render(
        hardwareAcceleration="nvidia", containerCgroupParent="media-containers.slice"
    )["services"]
    assert services["jellyfin"]["devices"] == ["nvidia.com/gpu=all"]
    assert all(
        value["cgroup_parent"] == "media-containers.slice"
        for value in services.values()
    )


def test_loopback_bind_address_does_not_duplicate_published_ports():
    services = render(bindAddress="127.0.0.1")["services"]
    assert (
        len(services["jellyfin"]["ports"]) == len(services["jellyseerr"]["ports"]) == 1
    )


def test_jellyseerr_configuration_and_cache_belong_to_the_configured_nix_owner():
    service = render()["services"]["jellyseerr"]
    assert service["user"] == "${PUID}:${PGID}"
    assert service["tmpfs"] == [
        "/app/.next/cache:uid=${PUID},gid=${PGID},mode=0700,size=67108864"
    ]


def test_provisioning_waits_for_every_application_api():
    from stack.provisioning import APPLICATION_URLS

    services = yaml.safe_load((ROOT / "compose.yaml").read_text())["services"]
    dependencies = services["configure"]["depends_on"]
    for application in APPLICATION_URLS:
        assert dependencies[application]["condition"] == "service_healthy"
