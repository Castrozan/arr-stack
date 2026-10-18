from pathlib import Path

from stack.bootstrap import create_file
from stack.onboarding_http import JsonClient


def onboard_jellyfin(password):
    client = JsonClient(
        "http://jellyfin:8096",
        {
            "X-Emby-Authorization": 'MediaBrowser Client="arr-stack", Device="Docker", DeviceId="arr-stack", Version="0.1.0"',
        },
    )
    information = client.request("GET", "/System/Info/Public")
    if not information["StartupWizardCompleted"]:
        client.request("GET", "/Startup/User")
        client.request(
            "POST",
            "/Startup/Configuration",
            {
                "UICulture": "en-US",
                "MetadataCountryCode": "BR",
                "PreferredMetadataLanguage": "en",
            },
        )
        client.request("POST", "/Startup/User", {"Name": "admin", "Password": password})
        client.request(
            "POST",
            "/Startup/RemoteAccess",
            {"EnableRemoteAccess": True, "EnableAutomaticPortMapping": False},
        )
        client.request("POST", "/Startup/Complete")
    token_file = Path("/state/jellyfin-api-key")
    if token_file.exists():
        client.headers["X-Emby-Token"] = token_file.read_text().strip()
        client.request("GET", "/System/Info")
        return
    account = client.request(
        "POST", "/Users/AuthenticateByName", {"Username": "admin", "Pw": password}
    )
    create_file(token_file, account["AccessToken"])
