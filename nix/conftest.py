import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ["ARR_ACCOUNT_POLICY_FILE"] = str(
    Path(__file__).parent / "test-fixtures/accounts.json"
)
os.environ["ARR_USERS_LIBRARY_ROOT"] = "/media"
os.environ["ARR_MEDIA_REQUESTER_USERNAME"] = "lucas"
sys.path.insert(0, str(ROOT / "runtime"))
