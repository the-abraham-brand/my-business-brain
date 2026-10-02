#!/usr/bin/env bash
# Build the shared test brain (a fictional company), then give it an identity and some promises.
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"
S="$D/../../skills/my-business-brain/scripts"
python3 "$D/../_fixtures/make_brain.py" ./business-brain
python3 "$S/identity.py" ./business-brain init --name Noor --owner Abraham >/dev/null
python3 "$S/commitments.py" ./business-brain add --what "Send Supplier X our renewal decision" --to "Supplier X" --due 2026-09-28 >/dev/null
python3 "$S/delegations.py" ./business-brain add --task "Collect three hosting quotes" --owner "Omar" --due 2026-09-29 >/dev/null
