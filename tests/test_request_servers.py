from unittest.mock import Mock

from stack import request_servers


def test_repeated_onboarding_omits_readonly_server_identifiers(monkeypatch):
    client = Mock()
    client.request.side_effect = lambda method, path, payload=None: (
        [{"id": 0, "hostname": path.rsplit("/", 1)[1], "is4k": False}]
        if method == "GET"
        else None
    )
    monkeypatch.setattr(
        request_servers, "desired_server", lambda app: {"hostname": app}
    )
    request_servers.configure_request_servers(client)
    updates = [call for call in client.request.call_args_list if call.args[0] == "PUT"]
    assert len(updates) == 2
    assert all("id" not in call.args[2] for call in updates)
    assert all(call.args[1].endswith("/0") for call in updates)
