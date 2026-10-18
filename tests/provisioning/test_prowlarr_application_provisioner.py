import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "runtime/arr_config_provisioner")
)

import prowlarr_application_provisioner as provisioner


def application(identifier, implementation, upstream, name=None):
    return {
        "id": identifier,
        "name": name or implementation,
        "implementation": implementation,
        "fields": [{"name": "baseUrl", "value": upstream}],
    }


def test_removes_only_retired_local_container_targets(monkeypatch):
    applications = [
        application(1, "Sonarr", "http://sonarr:8989"),
        application(2, "Lidarr", "http://lidarr:8686"),
        application(3, "Readarr", "http://readarr:8787"),
        application(4, "Lidarr", "http://music.example:8686", "Remote music"),
    ]
    deleted = []
    monkeypatch.setattr(provisioner, "get_resource_list", lambda *args: applications)
    monkeypatch.setattr(provisioner, "request_json", lambda *args: deleted.append(args))
    assert provisioner.remove_retired_applications(
        "http://prowlarr/api/v1", "key", [{"name": "Sonarr"}], False
    ) == ["Lidarr", "Readarr"]
    assert [request[1] for request in deleted] == [
        "http://prowlarr/api/v1/applications/2",
        "http://prowlarr/api/v1/applications/3",
    ]


def test_preserves_explicitly_declared_retired_application(monkeypatch):
    monkeypatch.setattr(
        provisioner,
        "get_resource_list",
        lambda *args: [application(2, "Lidarr", "http://lidarr:8686")],
    )
    assert (
        provisioner.remove_retired_applications(
            "base", "key", [{"name": "Lidarr"}], False
        )
        == []
    )


def test_dry_run_keeps_retired_target(monkeypatch):
    deleted = []
    monkeypatch.setattr(
        provisioner,
        "get_resource_list",
        lambda *args: [application(3, "Readarr", "http://readarr:8787")],
    )
    monkeypatch.setattr(provisioner, "request_json", lambda *args: deleted.append(args))
    assert provisioner.remove_retired_applications("base", "key", [], True) == [
        "Readarr"
    ]
    assert deleted == []
