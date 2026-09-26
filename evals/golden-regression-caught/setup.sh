#!/usr/bin/env bash
# Build the shared test brain (a fictional company), then add golden history.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/../_fixtures/make_brain.py" ./business-brain
python3 "$HERE/../_fixtures/add_state.py" ./business-brain golden
