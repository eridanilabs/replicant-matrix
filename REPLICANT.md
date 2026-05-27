# REPLICANT.md - Template

Copy this file to a new `replicant/<name>` branch. Fill in every field.
This file is a human-readable companion to AGENTS.md and replicant.env.
It is NOT loaded at runtime - it exists for documentation and easy diffing between branches.

---

<!-- BEGIN REPLICANT IDENTITY -->
**Agent**: <name>
**Workspace**: `/home/raykao/.copilot-bridge/workspaces/<name>`
**Beads**:
  - `BEADS_DIR="/home/raykao/.copilot-bridge/workspaces/<name>/.beads"`
  - `BEADS_ACTOR="<name>"`
**Branch prefix**: `<name>/`
**Worktree prefix**: `<name>-`
**Session handoff key prefix**: `session-handoff-<name>-`
**Channel**: <mattermost-channel>
**Base branch**: `replicant/<name>` in `eridanilabs/replicant-matrix`

## Role

<one paragraph describing what this replicant does and does not own>

## Domain Focus

<bullet list of repos and layers this replicant owns>

**Does NOT own**: <what to route elsewhere>

## Active Task Queue

<ordered list of Beads task IDs and titles, updated as tasks close>

## Domain Conventions

<any conventions specific to this replicant's domain>

## Coordination

<how this replicant coordinates with bill and other replicants>
<!-- END REPLICANT IDENTITY -->
