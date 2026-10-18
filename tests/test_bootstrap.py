import base64
import hashlib
import json
import os
import stat
from xml.etree.ElementTree import parse

import pytest

from stack.bootstrap import credentials, initialize


def test_initialize_preserves_secrets_api_keys_and_application_state(tmp_path):
    configuration, data, state = (
        tmp_path / name for name in ("config", "data", "state")
    )
    initialize(configuration, data, state)
    password = credentials(state)
    application_key = parse(configuration / "sonarr/config.xml").findtext("ApiKey")
    custom_file = configuration / "sonarr/custom.json"
    custom_file.write_text('{"existing":true}')
    initialize(configuration, data, state)
    assert credentials(state) == password
    assert (
        parse(configuration / "sonarr/config.xml").findtext("ApiKey") == application_key
    )
    assert custom_file.read_text() == '{"existing":true}'
    assert stat.S_IMODE((state / "credentials.json").stat().st_mode) == 0o600
    assert len(set(password.values())) == len(password)


def test_password_matches_qbittorrent_pbkdf2_configuration(tmp_path):
    configuration, data, state = (
        tmp_path / name for name in ("config", "data", "state")
    )
    initialize(configuration, data, state)
    password = credentials(state)["qbittorrent"]
    value = (configuration / "qbittorrent/qBittorrent/qBittorrent.conf").read_text()
    encoded = value.split("@ByteArray(", 1)[1].split(")", 1)[0]
    salt, digest = (base64.b64decode(part) for part in encoded.split(":"))
    assert hashlib.pbkdf2_hmac("sha512", password.encode(), salt, 100000) == digest


def test_state_loss_refuses_to_replace_existing_passwords(tmp_path):
    configuration, data, state = (
        tmp_path / name for name in ("config", "data", "state")
    )
    initialize(configuration, data, state)
    (state / "credentials.json").unlink()
    with pytest.raises(RuntimeError, match="Restore the state volume"):
        initialize(configuration, data, state)
    assert not (state / "credentials.json").exists()


def test_bazarr_connects_to_generated_application_keys(tmp_path):
    configuration, data, state = (
        tmp_path / name for name in ("config", "data", "state")
    )
    initialize(configuration, data, state)
    bazarr = json.loads((configuration / "bazarr/config/config.yaml").read_text())
    for app in ("sonarr", "radarr"):
        assert bazarr[app]["apikey"] == parse(
            configuration / app / "config.xml"
        ).findtext("ApiKey")
        assert bazarr[app]["ip"] == app
    source = data / "torrents/test.mkv"
    destination = data / "media/movies/test.mkv"
    source.write_bytes(b"media")
    os.link(source, destination)
    assert source.stat().st_ino == destination.stat().st_ino
