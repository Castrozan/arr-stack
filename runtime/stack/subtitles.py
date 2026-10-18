import os
import subprocess
import sys


def warm():
    environment = {
        **os.environ,
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BASE_URL": "http://jellyfin:8096",
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_API_KEY_FILE": "/state/jellyfin-api-key",
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_DATA_DIRECTORY": "/stack/config/jellyfin/data/data",
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_ITEM_BUDGET": "20",
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BUSY_ITEM_BUDGET": "1",
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_PAUSE_SECONDS": "2",
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_POLL_SECONDS": "10",
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_WAIT_SECONDS": "60",
    }
    raise SystemExit(
        subprocess.call(
            [sys.executable, "/app/runtime/jellyfin_subtitle_extraction_warmer"],
            env=environment,
        )
    )
