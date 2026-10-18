#!/usr/bin/env bash
set -euo pipefail
compose=(docker compose -p "arr-ci-${GITHUB_RUN_ID:-$(date +%s)}" -f compose.yaml -f tests/compose.smoke.yaml)
finish() {
	result=$?
	if ((result != 0)); then "${compose[@]}" logs --no-color --tail 150; fi
	"${compose[@]}" down
	exit "$result"
}
trap finish EXIT
"${compose[@]}" up -d --build --wait --wait-timeout 300
test "$(docker wait "$("${compose[@]}" ps --all --quiet configure)")" = 0
"${compose[@]}" run --rm -T manage onboard
"${compose[@]}" run --rm -T manage users create acceptance-friend >/dev/null
"${compose[@]}" run --rm -T --entrypoint python -v "$PWD/tests:/checks:ro" manage /checks/acceptance.py
"${compose[@]}" run --rm -T manage onboard
"${compose[@]}" down
"${compose[@]}" up -d --wait --wait-timeout 300
test "$(docker wait "$("${compose[@]}" ps --all --quiet configure)")" = 0
"${compose[@]}" run --rm -T --entrypoint python -v "$PWD/tests:/checks:ro" manage /checks/acceptance.py
