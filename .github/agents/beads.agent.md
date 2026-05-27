---
name: Beads Task Memory
description: Persistent task tracking for this workspace using bd (Beads). Use this skill to create, track, and close tasks across sessions.
---

# Beads Task Memory Skill

This workspace uses [Beads](https://github.com/steveyegge/beads) (`bd`) for persistent, structured task memory backed by Dolt. Tasks survive session restarts.

## Environment

Always ensure these are set before running `bd`:
- `BEADS_DIR=/home/raykao/.copilot-bridge/workspaces/bill/.beads`
- `BEADS_ACTOR=bill`

These are injected automatically via the workspace `.env` file.

## Session Start Workflow

Run at the beginning of every session to recover context:

```bash
bd prime              # Print workflow context and pending work
bd ready --json       # List tasks with no open blockers (what to work on next)
```

## Task Operations

### Creating tasks
```bash
bd create --title="Short descriptive title" --description="Why this exists and what needs to be done" --type=task --priority=2
```
- Types: `task`, `feature`, `bug`, `epic`, `chore`, `decision`
- Priority: `0` (critical) → `4` (backlog). Use numbers, not words.
- For descriptions with special chars, pipe via stdin: `echo "description" | bd create --title="Title" --stdin`
- **NEVER** use `bd edit` - it opens `$EDITOR` and blocks the agent.

#### Assignee field
Use `--assignee` with a **specific identifier**, not a generic role. This enables precise ownership tracking across multiple humans and multiple agent instances (each workspace/channel is an isolated agent context):

**Humans** - use their GitHub handle:
```bash
bd create --title="..." --assignee raykao
```

**Agents** - use `<bot-name>@<workspace>` format to identify which instance owns the task. The bot name and workspace are visible in the bridge config and channel context:
```bash
bd create --title="..." --assignee copilot@bill   # this agent, bill workspace
bd create --title="..." --assignee copilot@dm-raykao      # DM channel instance
```

**Shared ownership:**
```bash
bd create --title="..." --assignee "raykao+copilot@bill"
```

> **Why this matters:** Multiple agent instances run in isolated memory (different channels, DMs, workspaces). An agent in a DM has no awareness of work claimed by an agent in bill. Specific assignees make cross-instance ownership visible in the GitHub epic dashboard.

### Claiming and progressing work
```bash
bd update <id> --claim          # Atomically claim a task (sets assignee + in_progress)
bd update <id> --status=done    # Update status without closing
bd update <id> --notes="..."    # Add notes inline
```

**Before claiming a task**, read the parent epic issue body to check for human-set priorities or status changes:
```bash
gh issue view <epic-number> --repo eridanilabs/<repo> --json body --jq '.body'
```
This ensures the agent doesn't claim work a human has reprioritised or blocked since the last session.

### Closing tasks
```bash
bd close <id> --reason="What was done"
bd close <id1> <id2> <id3>     # Close multiple at once
```

**After closing a task**, update the corresponding row in the parent epic issue's task table to ✅ done.
Use the `gh-issue` skill (`.github/skills/gh-issue.md`) for the read → modify → write-back pattern:
```bash
BODY=$(gh issue view <epic-number> --repo eridanilabs/<repo> --json body --jq '.body')
UPDATED=$(echo "$BODY" | sed 's/| 🔄 in-progress | My Task |/| ✅ done | My Task |/')
gh issue edit <epic-number> --repo eridanilabs/<repo> --body "$UPDATED"
```

### Viewing and searching
```bash
bd show <id>           # Full task details + audit trail
bd list                # All open issues
bd list --status=in_progress   # Active work
bd search "keyword"    # Search issues
bd stats               # Project health summary
```

### Dependencies
```bash
bd dep add <child-id> <parent-id>   # child depends on parent (parent blocks child)
bd blocked                          # Show all blocked issues
```

### Persistent memory (cross-session knowledge)
```bash
bd remember "key insight or decision"    # Store persistent knowledge
bd memories "keyword"                    # Search stored memories
```

## Session End Workflow

Before ending a session, close completed tasks and back up:

```bash
bd close <id1> <id2> ...        # Close all completed work
bd backup export-git             # Snapshot to git branch (zero-infrastructure backup)
```

## When to Use Beads

- Any task that spans multiple tool calls or might be interrupted
- Multi-step work with subtasks (use epics + child tasks)
- Decisions that should be recorded for future sessions
- Anything you'd otherwise write to MEMORY.md

**Note**: `MEMORY.md` is deprecated in favour of Beads for task tracking. Use `bd remember` for persistent knowledge instead.

## GitHub Issue Sync

This agent integrates with GitHub Issues via the `gh-issue` skill (`.github/skills/gh-issue.md`).

### Sync Protocol
1. **Before claiming** - read the parent epic issue body to respect human-set priorities
2. **After closing** - update the epic task table row to ✅ done

### Assignee ↔ Label mapping
| Beads `--assignee` | GitHub label | Notes |
|--------------------|--------------|-------|
| `raykao` (or any GitHub handle) | `owner:human` | Specific human |
| `copilot@bill` (or `<bot>@<workspace>`) | `owner:agent` | Specific agent instance |
| `raykao+copilot@bill` | `owner:both` | Shared ownership |

Always use the `gh-issue` skill for all issue reads and writes. Never use MCP for GitHub Issue operations.

## Troubleshooting

```bash
bd doctor          # Check Dolt server health
bd dolt start      # Manually start Dolt server if needed
bd dolt status     # Check server status
```
