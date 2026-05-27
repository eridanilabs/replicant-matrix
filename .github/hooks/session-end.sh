#!/usr/bin/env bash
# session-end.sh
#
# Generic session-end hook for replicant-matrix agents.
# Sources replicant.env then runs Beads git backup.
set -euo pipefail

cat >/dev/null

export PATH="/home/raykao/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_FILE="$WORKSPACE_ROOT/replicant.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi

if [ -n "${BEADS_DIR:-}" ]; then
  export BEADS_DIR
fi
if [ -n "${BEADS_ACTOR:-}" ]; then
  export BEADS_ACTOR
fi

if command -v bd &>/dev/null; then
  bd backup export-git >/dev/null 2>&1 || true
fi

echo '{}'
