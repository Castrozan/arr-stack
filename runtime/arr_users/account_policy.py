import json
import os
from pathlib import Path


def account_names(field):
    path = Path(os.environ.get("ARR_ACCOUNT_POLICY_FILE", "/policy/accounts.json"))
    policy = json.loads(path.read_text(encoding="utf-8"))
    names = policy.get(field, [])
    if not isinstance(names, list) or any(
        not isinstance(name, str) or not name for name in names
    ):
        raise ValueError(f"{field} must contain account names")
    return tuple(names)
