#!/usr/bin/env bash
#
# deploy.sh — start the «Аким на 5 часов» simulator locally, listening on 0.0.0.0.
#
#   ./deploy.sh                 # http://<host>:8080/
#   PORT=9000 ./deploy.sh       # listen elsewhere
#   HOST=127.0.0.1 ./deploy.sh  # listen on loopback only
#
# Extra arguments are passed straight through to the app:
#   ./deploy.sh --port 9000     # same as PORT=9000
#
# Python 3.10+ is the only requirement; the app has no dependencies.
# Stop it with Ctrl+C.

set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

exec python3 -m src.web --host "${HOST:-0.0.0.0}" --port "${PORT:-8080}" "$@"
