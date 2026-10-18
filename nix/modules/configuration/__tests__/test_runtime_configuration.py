import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "runtime/arr_config_provisioner"))
SPECIFICATION = importlib.util.spec_from_file_location(
    "native_provisioning", Path(__file__).parents[1] / "scripts/provision.py"
)
NATIVE_PROVISIONING = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(NATIVE_PROVISIONING)


def test_native_provisioning_uses_host_addresses_and_runtime_api_keys(
    tmp_path, monkeypatch
):
    environment = tmp_path / "environment"
    environment.write_text("ARR_BIND_ADDR=192.0.2.10\n")
    for app in ("sonarr", "radarr"):
        configuration = tmp_path / "config" / app / "config.xml"
        configuration.parent.mkdir(parents=True)
        configuration.write_text(f"<Config><ApiKey>{app}-key</ApiKey></Config>")
    for name, value in {
        "ARR_PROVISIONER_ENV_FILE": str(environment),
        "ARR_PROVISIONER_CONFIG_ROOT": str(tmp_path / "config"),
        "ARR_BIND_ADDRESS_KEY": "ARR_BIND_ADDR",
        "ARR_PROVISIONER_JELLYSEERR_BASE_URL": "http://127.0.0.1:5055",
        "ARR_PROVISIONER_DESIRED_STATE_DIR": str(tmp_path),
    }.items():
        monkeypatch.setenv(name, value)
    settings = NATIVE_PROVISIONING.resolve_configuration()
    assert settings["application_urls"]["sonarr"] == "http://192.0.2.10:8989"
    assert settings["application_urls"]["radarr"] == "http://192.0.2.10:7878"
    assert settings["application_urls"]["prowlarr"] == "http://192.0.2.10:9696"
    assert settings["application_urls"]["qbittorrent"] == "http://192.0.2.10:8080"
    assert settings["secret_map"]["@RADARR_API_KEY@"] == "radarr-key"
