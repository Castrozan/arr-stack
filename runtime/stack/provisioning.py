from pathlib import Path

from arr_config_provisioner import provisioner_core
from arr_config_provisioner.runtime_config import (
    read_app_api_key,
    read_jellyseerr_api_key,
)
from stack.bootstrap import credentials
from stack.accounts import synchronize_accounts
from stack.configuration_lock import configuration_lock

APPLICATION_URLS = {
    "bazarr": "http://bazarr:6767",
    "radarr": "http://radarr:7878",
    "sonarr": "http://sonarr:8989",
    "prowlarr": "http://prowlarr:9696",
    "qbittorrent": "http://qbittorrent:8080",
}


def configuration():
    config_root = "/stack/config"
    values = credentials(Path("/state"))
    return {
        "application_urls": APPLICATION_URLS,
        "config_root": config_root,
        "jellyseerr_api_key": read_jellyseerr_api_key(config_root),
        "jellyseerr_base_url": "http://jellyseerr:5055",
        "desired_state_dir": "/app/defaults",
        "login_username": "admin",
        "login_passwords": {
            app: values[app] for app in ("sonarr", "radarr", "prowlarr")
        },
        "qbittorrent_username": "admin",
        "qbittorrent_password": values["qbittorrent"],
        "secret_map": {
            "@QBITTORRENT_PASSWORD@": values["qbittorrent"],
            "@SONARR_API_KEY@": read_app_api_key(config_root, "sonarr"),
            "@RADARR_API_KEY@": read_app_api_key(config_root, "radarr"),
        },
    }


def configure(dry_run=False):
    with configuration_lock():
        apply_configuration(dry_run)


def apply_configuration(dry_run):
    settings = configuration()
    plans = (
        (
            provisioner_core.BAZARR_CONFIGURATION_PLAN,
            provisioner_core.provision_bazarr_configuration_step,
            "subtitles",
        ),
        (
            provisioner_core.HOST_LOGIN_PLAN,
            provisioner_core.provision_host_login_step,
            "authentication",
        ),
        (provisioner_core.RESOURCE_PLAN, provisioner_core.provision_step, "resources"),
        (
            provisioner_core.QUALITY_PROFILE_PLAN,
            provisioner_core.provision_quality_profile_step,
            "profiles",
        ),
        (
            provisioner_core.QBITTORRENT_PREFERENCE_PLAN,
            provisioner_core.provision_qbittorrent_preference_step,
            "preferences",
        ),
    )
    failures = sum(
        provisioner_core.run_plan(settings, plan, runner, label, dry_run)
        for plan, runner, label in plans
    )
    if settings["jellyseerr_api_key"] and Path("/state/onboarding-complete").exists():
        failures += provisioner_core.run_plan(
            settings,
            provisioner_core.JELLYSEERR_SONARR_PROFILE_PLAN,
            provisioner_core.provision_jellyseerr_sonarr_profile_step,
            "request profiles",
            dry_run,
        )
        failures += provisioner_core.run_plan(
            settings,
            provisioner_core.JELLYSEERR_DOWNLOAD_TRACKING_PLAN,
            provisioner_core.provision_jellyseerr_download_tracking_step,
            "download tracking",
            dry_run,
        )
    if failures:
        raise SystemExit(
            f"Configuration failed in {failures} steps; inspect the preceding service errors."
        )
    if not dry_run and Path("/state/onboarding-complete").exists():
        synchronize_accounts()
    print("Opinionated configuration applied.")
