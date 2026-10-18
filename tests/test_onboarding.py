from unittest.mock import Mock
from contextlib import nullcontext

import pytest

from stack import jellyfin_onboarding, provisioning


def test_jellyfin_initializes_first_user_before_updating_it(monkeypatch, tmp_path):
    client = Mock()
    client.headers = {}
    client.request.side_effect = lambda method, path, payload=None: (
        {"StartupWizardCompleted": False}
        if path == "/System/Info/Public"
        else {"AccessToken": "test-token"}
        if path == "/Users/AuthenticateByName"
        else None
    )
    token_file = tmp_path / "token"
    monkeypatch.setattr(jellyfin_onboarding, "JsonClient", lambda *arguments: client)
    monkeypatch.setattr(jellyfin_onboarding, "Path", lambda path: token_file)
    jellyfin_onboarding.onboard_jellyfin("secret")
    calls = [(call.args[0], call.args[1]) for call in client.request.call_args_list]
    assert calls.index(("GET", "/Startup/User")) < calls.index(
        ("POST", "/Startup/User")
    )
    assert token_file.read_text() == "test-token"


def test_completed_jellyfin_setup_does_not_change_account_credentials(
    monkeypatch, tmp_path
):
    client = Mock()
    client.headers = {}
    client.request.return_value = {"StartupWizardCompleted": True}
    token_file = tmp_path / "token"
    token_file.write_text("existing-token")
    monkeypatch.setattr(jellyfin_onboarding, "JsonClient", lambda *arguments: client)
    monkeypatch.setattr(jellyfin_onboarding, "Path", lambda path: token_file)
    jellyfin_onboarding.onboard_jellyfin("unused")
    assert all(
        not call.args[1].startswith("/Startup/")
        for call in client.request.call_args_list
    )
    assert token_file.read_text() == "existing-token"


def test_configuration_failure_has_nonzero_exit_status(monkeypatch):
    monkeypatch.setattr(provisioning, "configuration_lock", nullcontext)
    monkeypatch.setattr(
        provisioning, "configuration", lambda: {"jellyseerr_api_key": ""}
    )
    monkeypatch.setattr(provisioning.provisioner_core, "run_plan", lambda *arguments: 1)
    with pytest.raises(SystemExit, match="Configuration failed in 5 steps"):
        provisioning.configure()
