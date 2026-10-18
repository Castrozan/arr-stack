import fcntl
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def configuration_lock(path=Path("/state/configure.lock"), timeout_seconds=300):
    deadline = time.monotonic() + timeout_seconds
    with path.open("a") as lock:
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        "Another configuration operation exceeded the five-minute wait bound"
                    )
                time.sleep(0.2)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
