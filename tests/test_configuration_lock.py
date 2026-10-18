import fcntl

import pytest

from stack.configuration_lock import configuration_lock


def test_competing_configuration_wait_is_bounded(tmp_path):
    path = tmp_path / "configure.lock"
    with path.open("a") as owner:
        fcntl.flock(owner, fcntl.LOCK_EX)
        with pytest.raises(RuntimeError, match="wait bound"):
            with configuration_lock(path, timeout_seconds=0):
                pytest.fail("Competing configuration acquired the owner's lock")
    with configuration_lock(path, timeout_seconds=0):
        assert path.exists()
