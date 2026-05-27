---
name: gh-issue
description: Interact with GitHub Issues in the eridanilabs org via the gh CLI
---

# GitHub Issue Skill (`gh-issue`)

This skill teaches the agent how to read, create, and update GitHub Issues in the **eridanilabs** GitHub organization using the `gh` CLI.

Always pass `--repo eridanilabs/<repo>` to every `gh` command, or export `GH_REPO=eridanilabs/<repo>` in the environment. The primary repos are:
- `eridanilabs/eridanilabs.github.io` (Hugo site)
- Other org repos as applicable

**Never use MCP for issue reads/writes** - always use `gh` CLI directly.

---

## Reading Issues

```bash
# Read a single issue (structured JSON - prefer this over raw text)
gh issue view <number> --repo eridanilabs/<repo> --json title,body,labels,state,number

# List all open issues
gh issue list --repo eridanilabs/<repo>

# List issues with a given label
gh issue list --repo eridanilabs/<repo> --label epic

# List issues assigned to a user
gh issue list --repo eridanilabs/<repo> --assignee <username>
```

---

## Creating Issues

```bash
# Create non-interactively
gh issue create \
  --repo eridanilabs/<repo> \
  --title "[FEAT] My feature title" \
  --body "$(cat body.md)" \
  --label feature

# Create an epic
gh issue create \
  --repo eridanilabs/<repo> \
  --title "[EPIC] My epic title" \
  --body "$(cat body.md)" \
  --label epic
```

---

## Updating Issues

```bash
# Overwrite the entire issue body (always read first - see below)
gh issue edit <number> --repo eridanilabs/<repo> --body "..."

# Add a label
gh issue edit <number> --repo eridanilabs/<repo> --add-label "status:in-progress"

# Remove a label
gh issue edit <number> --repo eridanilabs/<repo> --remove-label "status:in-progress"

# Close an issue
gh issue close <number> --repo eridanilabs/<repo>

# Reopen an issue
gh issue reopen <number> --repo eridanilabs/<repo>
```

---

## Updating a Section of the Issue Body (Read - Modify - Write Back)

Issue bodies are **full overwrites** - always read first, modify in memory, then write back:

```bash
# Step 1 - read the current body
BODY=$(gh issue view <number> --repo eridanilabs/<repo> --json body --jq '.body')

# Step 2 - modify the relevant section (using sed, awk, or Python for complex edits)
UPDATED_BODY=$(echo "$BODY" | sed 's/| pending | My Task |/| done | My Task |/')

# Step 3 - write back
gh issue edit <number> --repo eridanilabs/<repo> --body "$UPDATED_BODY"
```

For complex edits, prefer a small Python or bash script over inline sed to avoid quoting issues.

---

## Task Table Format (Epic Issues)

```markdown
| Status | Title | Beads ID | GH # | Owner |
|--------|-------|----------|------|-------|
| pending | Short task title | bill-001 | #12 | bill |
| in-progress | Another task | bill-002 | #13 | human |
| done | Completed task | bill-003 | #14 | bill |
| blocked | Blocked task | bill-004 | #15 | both |
```

Status values: `pending`, `in-progress`, `done`, `blocked`

---

## Labels

```bash
# Create a label (idempotent with --force)
gh label create "epic" --repo eridanilabs/<repo> --color "6E40C9" --description "Epic tracking issue" --force

# List all labels
gh label list --repo eridanilabs/<repo>
```

---

## Notes

- Issue body updates are **full overwrites** - always read first, modify in memory, then write back.
- Use `--json` output for programmatic processing; use default output for human-readable display.
- For bulk updates across multiple issues, script them with `gh issue list --json | jq` pipelines.
