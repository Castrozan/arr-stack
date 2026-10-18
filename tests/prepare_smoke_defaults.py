import json
import shutil
import sys
from pathlib import Path


def prepare_defaults(destination):
    shutil.copytree(
        Path(__file__).resolve().parents[1] / "defaults",
        destination,
        dirs_exist_ok=True,
    )
    path = destination / "prowlarr/indexer.json"
    indexers = json.loads(path.read_text())
    for indexer in indexers:
        indexer["enable"] = False
    path.write_text(json.dumps(indexers))


if __name__ == "__main__":
    prepare_defaults(Path(sys.argv[1]))
