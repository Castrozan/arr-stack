import json
import shutil
import sys
from pathlib import Path


def render_desired_state(source, private_indexer, destination):
    shutil.copytree(source, destination)
    indexers = destination / "prowlarr/indexer.json"
    objects = json.loads(indexers.read_text())
    objects.append(json.loads(private_indexer.read_text()))
    indexers.write_text(json.dumps(objects, indent=2) + "\n")
    for app in ("sonarr", "radarr"):
        path = destination / app / "notification.json"
        path.write_text(
            path.read_text().replace("http://cleanup:8789/", "http://172.28.0.1:8789/")
        )


if __name__ == "__main__":
    render_desired_state(*(Path(value) for value in sys.argv[1:]))
