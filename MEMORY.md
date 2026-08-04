# Memory

> **DEPRECATED:** This file is no longer the primary memory store.
> Use `bd remember` and `bd memories <keyword>` instead.
> This file will not be updated going forward.

## Carried over from `raykao/goku` at migration time

The following was in goku's MEMORY.md before migration to this branch. Verify against
Beads and re-file via `bd remember` rather than continuing to edit this file.

**Recall migrated memories** (search Beads once goku's `bd` workspace is live):
```bash
bd memories scut              # SCUT project, arch, phase status, UI state, UI gotchas
bd memories cbk               # CBK ACP lineage, hanging bug, code issues
bd memories beads             # CLI gotchas
bd memories dark-factory      # dashboard conventions
bd memories session-handoff-goku   # latest session handoff
```

### Active work at time of migration [2026-05-25]

**Branch:** `bill/docs/cbk-merge-plan` in `workbench/bill-cbk-merge-plan/`
**PR #8:** https://github.com/eridanilabs/scut/pull/8

Draft 5 of the merge spec had two known issues (phase numbering gap, section 4.4
content gap) - see AGENTS.md's REPLICANT IDENTITY block "Active Task Queue" for details.

### Key decisions to re-file in Beads

- `scut-run-dropped-decision-2026-05-25` - Run dropped, AgentTask at boundary + comment_dispatches sidecar
- `scut-api-first-constraint-2026-05-25` - all routes /api/v1/, reverse proxy, curl-first gate
- `scut-deployment-topology-2026-05-25` - Caddy/nginx in infra/dev/, SPA fallback, smoke.sh
- `scut-curl-first-testability-2026-05-25` - server+test+OpenAPI PR before UI PR
- `scut-acp-naming-correction-2026-05-25` - ACP = Agent Client Protocol (agentclientprotocol.com)
  JSON-RPC 2.0. SCUT=Client, harnesses=Agent subprocesses. NOT IBM ACP. AcpConnector PRIMARY
  outbound; CopilotBridge legacy; A2A INBOUND only at /api/v1/a2a/...
