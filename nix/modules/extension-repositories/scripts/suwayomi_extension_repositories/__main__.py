import sys
import urllib.error

import extension_repository_synchronization
import runtime_configuration


def report_repository_synchronization(synchronized):
    if synchronized["repositories"] is None:
        print(
            f"no declared repository list at {runtime_configuration.declared_repository_list_file()}, "
            "so Suwayomi's own repositories were left alone"
        )
    elif not synchronized["rewritten"]:
        print("already declared, nothing rewritten")
    elif synchronized["extensions_offered"] is None:
        print(
            "repositories rewritten, but Suwayomi could not index them right now; "
            "it retries on its own and the declared list is already stored"
        )
    else:
        print(f"extensions now offered: {synchronized['extensions_offered']}")


def main():
    try:
        synchronized_repositories = (
            extension_repository_synchronization.synchronize_extension_repositories()
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    except urllib.error.URLError as error:
        print(f"cannot reach Suwayomi: {error.reason}", file=sys.stderr)
        raise SystemExit(1) from error
    report_repository_synchronization(synchronized_repositories)


if __name__ == "__main__":
    main()
