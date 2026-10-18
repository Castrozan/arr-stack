import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from stack.bootstrap import initialize


def package_command(package, arguments):
    raise SystemExit(
        subprocess.call(
            [sys.executable, str(Path(__file__).parent / package), *arguments]
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Configure and operate the opinionated Docker media stack"
    )
    parser.add_argument(
        "command",
        choices=(
            "initialize",
            "credentials",
            "configure",
            "onboard",
            "users",
            "status",
            "cleanup",
            "subtitles",
        ),
    )
    arguments, remaining = parser.parse_known_args()
    if arguments.command in ("users", "status"):
        os.environ.update(
            {
                "ARR_STATUS_RADARR_BASE_URL": "http://radarr:7878",
                "ARR_STATUS_SONARR_BASE_URL": "http://sonarr:8989",
            }
        )
        package_command(
            {"users": "arr_users", "status": "arr_status"}[arguments.command],
            remaining,
        )
    if remaining and not (
        arguments.command == "configure" and remaining == ["--dry-run"]
    ):
        parser.error(f"unexpected arguments: {' '.join(remaining)}")
    if arguments.command == "initialize":
        initialize()
    elif arguments.command == "credentials":
        values = json.loads(Path("/state/credentials.json").read_text())
        for app, password in values.items():
            print(f"{app}: admin / {password}")
        print("Jellyseerr uses the Jellyfin account and password.")
    elif arguments.command == "configure":
        from stack.provisioning import configure

        configure(dry_run="--dry-run" in remaining)
    elif arguments.command == "onboard":
        from stack.onboarding import onboard

        onboard()
    elif arguments.command == "cleanup":
        from stack.cleanup_service import serve

        serve()
    elif arguments.command == "subtitles":
        from stack.subtitles import warm

        warm()


if __name__ == "__main__":
    main()
