import logging
import os
import threading
from http.server import HTTPServer
from pathlib import Path

from arr_config_provisioner.runtime_config import read_app_api_key
from download_cleanup.clients import JellyfinClient, MediaClient, TorrentClient
from download_cleanup.filesystem import Filesystem
from download_cleanup.jellyfin_artifacts import JellyfinArtifacts
from download_cleanup.ledger import Ledger
from download_cleanup.server import webhook_handler
from download_cleanup.worker import CleanupWorker
from stack.bootstrap import credentials
from stack.provisioning import APPLICATION_URLS


def serve():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    password = credentials(Path("/state"))["qbittorrent"]
    ledger = Ledger(Path("/cleanup-state/cleanup.sqlite"))
    clients = {
        app: MediaClient(
            f"{APPLICATION_URLS[app]}/api/v3",
            read_app_api_key("/stack/config", app),
            app,
        )
        for app in ("radarr", "sonarr")
    }
    token_file = Path("/state/jellyfin-api-key")
    token = token_file.read_text().strip() if token_file.exists() else ""
    worker = CleanupWorker(
        ledger,
        clients,
        TorrentClient(APPLICATION_URLS["qbittorrent"], "admin", password),
        Filesystem("/data"),
        JellyfinClient(
            "http://jellyfin:8096",
            token,
            JellyfinArtifacts(Path("/stack/config/jellyfin")),
        ),
    )
    wake_worker = threading.Event()

    def run_worker():
        try:
            while True:
                wake_worker.clear()
                if token_file.exists():
                    worker.jellyfin = JellyfinClient(
                        "http://jellyfin:8096",
                        token_file.read_text().strip(),
                        JellyfinArtifacts(Path("/stack/config/jellyfin")),
                    )
                worker.run_pending()
                wake_worker.wait(30)
        except Exception:
            logging.exception("Cleanup worker failed")
            os._exit(1)

    threading.Thread(target=run_worker, daemon=True).start()
    logging.info("Listening for native Radarr/Sonarr lifecycle webhooks")
    HTTPServer(
        ("0.0.0.0", 8789), webhook_handler(ledger, password, wake_worker)
    ).serve_forever()
