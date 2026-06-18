#!/usr/bin/env bash
# session-end.sh
#
# Generic session-end hook for replicant-matrix agents.
# Sources .env + replicant.env, derives BEADS_DIR, then runs Beads git backup.
set -euo pipefail

cat >/dev/null

export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

set -a
# Source workspace .env first (bridge-written, may set an explicit BEADS_DIR)
[ -f "$WORKSPACE_ROOT/.env" ] && source "$WORKSPACE_ROOT/.env"
# Source replicant.env if present (agent-specific values: actor, dolt user)
[ -f "$WORKSPACE_ROOT/replicant.env" ] && source "$WORKSPACE_ROOT/replicant.env"
set +a

# Derive BEADS_DIR from the bridge home + actor when not explicitly provided.
BRIDGE_HOME="${COPILOT_BRIDGE_HOME:-$HOME/.copilot-bridge}"
if [ -z "${BEADS_DIR:-}" ] && [ -n "${BEADS_ACTOR:-}" ]; then
  BEADS_DIR="$BRIDGE_HOME/workspaces/$BEADS_ACTOR/.beads"
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
