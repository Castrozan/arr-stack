import importlib.util
import json
from pathlib import Path

SPECIFICATION = importlib.util.spec_from_file_location(
    "render_desired_state",
    Path(__file__).resolve().parents[1] / "render_desired_state.py",
)
RENDERER = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(RENDERER)


def test_nix_store_defaults_can_be_adapted_without_modifying_the_source(tmp_path):
    source = tmp_path / "defaults"
    for application in ("sonarr", "radarr"):
        (source / application).mkdir(parents=True)
        notification = source / application / "notification.json"
        notification.write_text('{"url":"http://cleanup:8789/delete"}')
        notification.chmod(0o444)
        notification.parent.chmod(0o555)
    (source / "prowlarr").mkdir()
    indexers = source / "prowlarr/indexer.json"
    indexers.write_text('[{"name":"public"}]')
    indexers.chmod(0o444)
    indexers.parent.chmod(0o555)
    source.chmod(0o555)
    private_indexer = tmp_path / "private.json"
    private_indexer.write_text('{"name":"private"}')
    destination = tmp_path / "rendered"

    RENDERER.render_desired_state(source, private_indexer, destination)

    assert json.loads((destination / "prowlarr/indexer.json").read_text()) == [
        {"name": "public"},
        {"name": "private"},
    ]
    for application in ("sonarr", "radarr"):
        assert json.loads(
            (destination / application / "notification.json").read_text()
        ) == {"url": "http://172.28.0.1:8789/delete"}
        assert (
            "http://cleanup:8789/"
            in (source / application / "notification.json").read_text()
        )
    assert json.loads(indexers.read_text()) == [{"name": "public"}]
