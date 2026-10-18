import io
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "runtime/arr_config_provisioner")
)

from bazarr_api_client import read_bazarr_api_key
import bazarr_api_client


@pytest.mark.parametrize(
    "content",
    [
        'auth:\n  apikey: "expected"\n  type: form\ngeneral:\n  apikey: other\n',
        "assrt:\n  apikey: wrong\nauth:\n  apikey: expected\ngeneral:\n  other: true\n",
        json.dumps({"auth": {"apikey": "expected"}}),
    ],
)
def test_reads_only_the_authentication_api_key(tmp_path, content):
    path = tmp_path / "bazarr/config/config.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(content)
    assert read_bazarr_api_key(tmp_path) == "expected"


def test_rejects_missing_authentication_key(tmp_path):
    path = tmp_path / "bazarr/config/config.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("assrt:\n  apikey: wrong\n")
    with pytest.raises(ValueError, match="API key is missing"):
        read_bazarr_api_key(tmp_path)


def test_submits_repeated_form_values_and_boolean_settings(monkeypatch):
    requests = []

    def open_request(request, timeout):
        requests.append(request)
        return io.BytesIO(b"")

    monkeypatch.setattr(bazarr_api_client, "urlopen", open_request)
    client = bazarr_api_client.BazarrApiClient("http://bazarr:6767/", "test-key")
    assert (
        client.request(
            "system/settings",
            {
                "languages-enabled": ["en", "pb"],
                "settings-general-movie_default_enabled": True,
            },
        )
        is None
    )
    request = requests[0]
    assert request.full_url == "http://bazarr:6767/api/system/settings"
    assert request.get_method() == "POST"
    assert parse_qs(request.data.decode()) == {
        "languages-enabled": ["en", "pb"],
        "settings-general-movie_default_enabled": ["true"],
    }
