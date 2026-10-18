import subprocess
import sys


def users(*arguments):
    subprocess.run([sys.executable, "/app/runtime/arr_users", *arguments], check=True)


def synchronize_accounts():
    for command in ("sync", "sync-account-permissions", "sync-request-routing"):
        users(command)
