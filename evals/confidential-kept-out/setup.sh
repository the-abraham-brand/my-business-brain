#!/usr/bin/env bash
# Build the shared test brain (a fictional company) in the run's empty workspace.
set -euo pipefail
python3 "$(cd "$(dirname "$0")" && pwd)/../_fixtures/make_brain.py" ./business-brain
