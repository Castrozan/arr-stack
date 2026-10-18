import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def read_bazarr_api_key(config_root):
    content = (Path(config_root) / "bazarr/config/config.yaml").read_text()
    try:
        api_key = json.loads(content).get("auth", {}).get("apikey", "")
    except json.JSONDecodeError:
        section = re.search(r"(?m)^auth:\s*\n((?:[ \t].*\n|\n)*)", content)
        match = (
            re.search(r"(?m)^\s+apikey:\s*['\"]?([a-zA-Z0-9]+)['\"]?\s*$", section[1])
            if section
            else None
        )
        api_key = match[1] if match else ""
    if not api_key:
        raise ValueError("Bazarr API key is missing from its authentication settings")
    return api_key


class BazarrApiClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def request(self, path, form=None):
        headers = {"X-API-KEY": self.api_key}
        payload = None
        if form is not None:
            values = {
                key: str(value).lower() if isinstance(value, bool) else value
                for key, value in form.items()
            }
            payload = urlencode(values, doseq=True).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = Request(f"{self.base_url}/api/{path}", data=payload, headers=headers)
        with urlopen(request, timeout=30) as response:
            content = response.read()
        return json.loads(content) if content else None
