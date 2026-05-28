#!/usr/bin/env bash
# session-start.sh
#
# Generic session-start hook for replicant-matrix agents.
# Sources replicant.env (two levels up from .github/hooks/) if present,
# then injects handoff state and top open tasks into additionalContext.
#
# Output: { "additionalContext": "<text>" } consumed by copilot-bridge SDK.
set -euo pipefail

cat >/dev/null

export PATH="/home/raykao/.local/bin:$PATH"

# Source env files - sets AGENT_NAME, BEADS_DIR, BEADS_ACTOR, BEADS_DOLT_PASSWORD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

set -a
# Source workspace .env first (always present, loaded by bridge)
[ -f "$WORKSPACE_ROOT/.env" ] && source "$WORKSPACE_ROOT/.env"
# Source replicant.env if present (may override with agent-specific values)
[ -f "$WORKSPACE_ROOT/replicant.env" ] && source "$WORKSPACE_ROOT/replicant.env"
set +a

ENV_FILE="$WORKSPACE_ROOT/replicant.env"

# Require BEADS_DIR and BEADS_ACTOR to be set (from replicant.env or environment)
if [ -z "${BEADS_DIR:-}" ] || [ -z "${BEADS_ACTOR:-}" ]; then
  echo '{}'
  exit 0
fi

export BEADS_DIR
export BEADS_ACTOR

if ! command -v bd &>/dev/null; then
  echo '{}'
  exit 0
fi

bd prime >/dev/null 2>&1 || true

HANDOFF_KEY=$(bd memories "session-handoff-${BEADS_ACTOR}-" --json 2>/dev/null \
  | jq -r "keys[]? | select(startswith(\"session-handoff-${BEADS_ACTOR}-\"))" \
  | sort | tail -1 || true)

ENV_INSTRUCTION="Before running any bd command this session, source your replicant.env: \`source ${ENV_FILE}\`"

if [ -z "$HANDOFF_KEY" ]; then
  jq -n --arg ctx "$ENV_INSTRUCTION" '{additionalContext: $ctx}'
  exit 0
fi

HANDOFF_BODY=$(bd recall "$HANDOFF_KEY" 2>/dev/null || true)
if [ -z "$HANDOFF_BODY" ]; then
  jq -n --arg ctx "$ENV_INSTRUCTION" '{additionalContext: $ctx}'
  exit 0
fi

READY=$(bd ready --json 2>/dev/null \
  | jq -r '.[]? | "  - \(.id // "?"): \(.title // "(untitled)")"' 2>/dev/null \
  | head -10 || true)
[ -z "$READY" ] && READY="  (none)"

CONTEXT=$(cat <<HANDOFF
## Session Resume State

The following was auto-injected by the sessionStart hook from Beads (source of truth).

**Environment**: Run \`source ${ENV_FILE}\` before any bd command this session.

**Latest handoff** (\`$HANDOFF_KEY\`):

$HANDOFF_BODY

**Top open Beads tasks:**

$READY

You are resuming a prior session. On your first turn, briefly acknowledge the handoff and confirm scope with the user before starting new work. If the user's first message is unrelated to the handoff, treat it as background context and proceed with their request.
HANDOFF
)

jq -n --arg ctx "$CONTEXT" '{additionalContext: $ctx}'
