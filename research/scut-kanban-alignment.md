# SCUT / copilot-bridge-kanban Alignment

**Status:** Complete
**Date:** 2025-07-15
**Question:** Where do `eridanilabs/scut` and `raykao/copilot-bridge-kanban` overlap, where do they diverge, and what is the best path to converge them into a single canonical repo?
**Informs:** Decision on which codebase to designate canonical and how to unify work going forward.

---

## Summary

Both repos implement the same core abstraction: a kanban-style work-item tracker with an embedded agent dispatch loop backed by SQLite and Fastify. The kanban repo is ahead on working software - it has live SSE, a functioning ACP connector, bridge streaming, run-resume, and checkpoints. SCUT is ahead on design - its spec articulates a richer data hierarchy (Project > Board > Column > Thread), a clean connector interface (`IReplicantConnector`), and a repository pattern that is absent from kanban. The current SCUT implementation code lags behind its own spec: the live schema has only 4 tables (replicants, threads, messages, runs) versus the 10-table full spec schema. **Recommendation: keep SCUT as the canonical repo and pull the kanban's working subsystems in as phased additions.** The kanban repo's SSE manager, ACP session manager, bridge streaming layer, checkpoint model, and run-resume endpoint are the four things SCUT needs that it does not yet have. SCUT's spec hierarchy, connector interface, and repository pattern are the four things SCUT has that kanban lacks and should not be discarded.

---

## Context

Both repos are owned by the same operator. The kanban repo was built as a standalone UI for copilot-bridge and has evolved a live agent integration layer. SCUT was conceived as the longer-term coordination plane with a full spec. They have converged on the same data model from different directions and now represent redundant investment. Continuing to develop both is wasteful; a decision on which to keep is needed before either is extended further.

---

## What We Know

### SCUT (`eridanilabs/scut`)

**Stack:** Fastify 5 + better-sqlite3 + TypeScript + React 19 + Vite, monorepo (`packages/server`, `packages/ui`).

**Current live schema** (4 tables, `packages/server/src/db/schema.sql`):

| Table | Key columns |
|-------|-------------|
| `replicants` | id (nanoid), name, harness, config (JSON), status |
| `threads` | id, title, description, status (idea/refining/ready/in_progress/blocked/done/archived), replicant_id |
| `messages` | id, thread_id, run_id, author (human/replicant/system), author_id, content |
| `runs` | id, thread_id, replicant_id, status (created/queued/running/completed/failed/cancelled), input, output, error |

**Spec schema** (10 tables, `docs/spec/spec.md` section 6.2 - NOT yet live):

projects, users, boards, columns, threads, comments, checklists, checklist_items, replicants, runs

The spec schema adds: full Org/Project/Board/Column hierarchy, User accounts, Checklists + ChecklistItems, and renames `messages` to `comments` with `author_type` (user/replicant/system).

**Live routes:**

- `GET/POST /api/threads`, `GET/PATCH/DELETE /api/threads/:id`
- `GET/POST /api/threads/:threadId/messages`
- `GET/POST /api/threads/:threadId/runs`, `GET /api/runs/:id`
- `GET/POST/PATCH/DELETE /api/replicants`, `GET /api/replicants/:id`
- `POST /api/internal/runs/:id/result` (connector callback)

**Connector architecture:**

- `IReplicantConnector` interface: `dispatch(run, thread)`, `cancel(runId)`, `status()`
- `CopilotBridgeConnector` implements it (webhook POST, fire-and-forget)
- `ConnectorRegistry` is a `Map<replicantId, IReplicantConnector>` loaded at startup
- Connectors post results back to `/api/internal/runs/:id/result`

**Auth:** Not yet implemented in the current server code (no middleware visible in routes). The spec defines JWT HS256 auth. The UI has a `LoginPage.tsx` and `auth.ts` store.

**UI pages:** `LoginPage`, `ProjectsPage`, `MootPage` (board), `ThreadDetailPage`, `ReplicantsPage`

**UI stores:** auth, boards, dm, projects, replicants, theme, threads, ui

**What is NOT live yet:** projects, boards, columns, users, checklists, checklist_items, SSE, auth middleware on routes, OpenAPI docs, full spec schema.

---

### copilot-bridge-kanban (`raykao/copilot-bridge-kanban`)

**Stack:** Fastify 5 + better-sqlite3 + TypeScript + React 19 + Vite, single package (`src/server`, `src/client`). Node >= 22, `"type": "module"`.

**Live schema** (9 tables, `src/server/db.ts`):

| Table | Key columns |
|-------|-------------|
| `users` | id (UUID), username, password_hash, created_at |
| `sessions` | id, user_id, expires_at (7-day rolling, server-side) |
| `preferences` | user_id, data (JSON) |
| `agent_tokens` | id, agent_name, token_hash, card_id (per-card per-agent tokens) |
| `cards` | id (UUID), type (work/chat), agent_bot (name), title, description, status (idea/...), created_by, workspace_subdir, metadata (JSON), archived_at |
| `card_labels` | card_id, label (N:N, separate table) |
| `card_comments` | id, card_id, author_kind (human/agent/system), author_id, content, run_id |
| `runs` | id, card_id, agent_name, status (created/running/awaiting/completed/failed/cancelled), bridge_run_id, input_comment_id, error, finished_at |
| `checkpoints` | id, card_id, name, turn_index, git_ref, created_by |

Plus a migration-managed `agents` table (added via `003-agents-table.ts`):

| Table | Key columns |
|-------|-------------|
| `agents` | id (UUID), name, protocol (acp), url, auto_approve (bool) |

**Live routes:**

- `GET/POST /api/cards`, `GET/PATCH/DELETE /api/cards/:id`
- `GET/POST /api/cards/:id/comments`
- `POST /api/cards/:id/comments` (triggers agent dispatch if card.agent_bot is set)
- `GET /api/cards/:id/runs`, `GET /api/cards/:id/runs/:run_id`
- `POST /api/cards/:id/runs/:run_id/resume` (bridge tool-call approval gate)
- `POST/DELETE /api/cards/:id/labels/:label`, `POST /api/cards/:id/labels`
- `GET/POST/DELETE /api/cards/:id/checkpoints`
- `GET /api/cards/:id/events` (SSE per card)
- `GET /api/events` (global SSE)
- `GET /api/agents`, `GET /api/agents/:name` (proxy to copilot-bridge)
- `GET/POST/PATCH/DELETE /api/admin/agents` (CRUD for registered ACP agents)
- `POST /api/auth/login`, `POST /api/auth/logout`
- Bridge push-callback routes (inbound webhook from copilot-bridge)

**Agent integration (both live and working):**

1. `CardSessionManager` + `BridgeStream`: SSE stream from copilot-bridge. Handles run.queued, run.in_progress, run.awaiting, message.part, message.completed, tool.start, tool.end. Emits card SSE events to UI.
2. `AcpSessionManager`: WebSocket + JSON-RPC 2.0 to ACP agents. Full async lifecycle: open socket, send tasks/send, stream notifications, close.
3. Per-card per-agent bearer tokens (`agent_tokens` table) for secure agent callbacks.

**Auth:** Cookie-based server-side sessions (not JWT). `@fastify/cookie` + bcrypt 12 rounds. 7-day sliding window. CLI for user management.

**UI pages:** `BoardPage`, `BacklogPage`, `CardDetailPage`, `ChatPage`, `CardListPage`, `SettingsPage`, `LoginPage`

**What the kanban does NOT have:** Project/Board/Column hierarchy, polymorphic assignee model, IReplicantConnector interface, repository pattern, OpenAPI docs, checklist/sub-task concept, thread parentage, PostgreSQL migration path.

---

## What We Don't Know

1. Whether the operator wants to keep the SCUT brand and vocabulary ("Thread", "Replicant", "Moot", "Comment") or switch to kanban vocabulary ("Card", "Agent", "Board", "Comment").
2. Whether "checkpoints" (git_ref + turn_index) belong in the canonical data model or are a copilot-bridge-specific concept.
3. Whether `card.type = 'work' | 'chat'` is a distinction worth keeping in the canonical model, or whether all threads/cards are the same type.
4. Whether the Project/Board/Column hierarchy from the SCUT spec is desired for v1, or whether a single flat list with filter views is sufficient for the near term.
5. Whether session-cookie auth or JWT is preferred for the canonical system.

---

## Options / Approaches

| Option | Description | Pros | Cons | Complexity |
|--------|-------------|------|------|-----------|
| **A** | Absorb kanban into SCUT. SCUT becomes canonical. Port kanban's working subsystems into SCUT's architecture. | Preserves SCUT's design, hierarchy, connector interface, repository pattern. Keeps the stronger long-term architecture. | More work to port; kanban's working agent code must be adapted to the IReplicantConnector interface. | Medium-high. |
| **B** | Absorb SCUT into kanban. Kanban becomes canonical. Add spec hierarchy on top of existing kanban. | Kanban's working code ships faster; existing Docker image, CLI, SSE, ACP all work today. | Kanban was not designed for the hierarchy; adding Board/Column/Project on top of flat cards is a layering exercise. Loses connector interface. | Medium. |
| **C** | Cherry-pick into a new unified repo. Start fresh, take best of each. | Clean slate; can pick the best of each. | Creates a third repo; doubles migration risk; loses git history continuity. | High. |

---

## Analysis

**What SCUT has that kanban needs:**

1. `IReplicantConnector` interface + `ConnectorRegistry` - the abstraction that makes harnesses swappable without touching route handlers. The kanban's `CardSessionManager` and `AcpSessionManager` are concrete, not abstracted; adding a third connector type requires modifying the dispatch branch in `card-routes.ts`.
2. Repository pattern (`IRepository`, `IThreadRepository`, etc.) - the seam that allows PostgreSQL to be swapped in. The kanban's DB access is direct function calls scattered across route handlers.
3. Project/Board/Column hierarchy with filter-rule columns. No equivalent exists in kanban. The operator's stated goal is a SaaS/managed service; a flat card list does not scale to multi-project, multi-team use.
4. Spec and OpenAPI documentation commitment. The kanban has a `plan.md` and `tasks.md` but no formal spec or API contract.

**What kanban has that SCUT needs:**

1. `SseManager` - complete SSE implementation with per-card and global subscriptions, heartbeat, and graceful shutdown. SCUT's spec has SSE in Phase 3; the kanban already ships it.
2. `BridgeStream` + `CardSessionManager` - the actual streaming integration with copilot-bridge. Handles all bridge event types including tool-call approval (`run.awaiting`). SCUT's `CopilotBridgeConnector` is a webhook stub; it does not stream.
3. `AcpSessionManager` - a live, tested ACP connector over WebSocket/JSON-RPC 2.0. SCUT's spec lists `ACPConnector` as Phase 5; kanban already has it.
4. Run-resume endpoint - `POST /api/cards/:id/runs/:run_id/resume` for human-in-the-loop tool call approval. Not in SCUT spec at all.
5. Checkpoints - `checkpoints` table with `git_ref` and `turn_index`. Valuable for copilot-bridge workflows; not in SCUT spec.
6. Per-card agent tokens (`agent_tokens` table). Security feature for multi-agent setups.
7. Working auth with session cookies and CLI user management.
8. Migrations runner (`src/server/migrations.ts` + `src/server/migrations/`) - additive schema changes via numbered migration files.

**On the architectural question:**

The SCUT spec's key design insight - "Columns are Views, Not Containers" and polymorphic assignee - is more correct for the long term than the kanban's implicit approach (status field for column, agent_bot string for assignee). Both choices are compatible at the data layer: the kanban's `cards.status` is exactly what SCUT's `threads.status` is, and the kanban's `cards.agent_bot` is a simplified version of SCUT's `assignee_type + assignee_id`. Migration between the two schemas would require:

- Rename `cards` to `threads`, add `project_id` FK, add `assignee_type` (= 'replicant' where `agent_bot` is set, null otherwise), add `assignee_id` (= agents.id resolved from `agent_bot` name)
- Rename `card_comments` to `comments`, rename `author_kind` to `author_type`, rename `author_id` (no-op)
- Rename `card_labels` to keep as-is or fold into `metadata.labels` (the SCUT spec convention)
- Move `agent_tokens` → keep as-is
- Add `projects`, `boards`, `columns`, `users` tables
- Map existing `agents` table to `replicants`

This migration is mechanical, not architectural. None of the data is lost; the shape changes.

**Auth divergence:**

Kanban uses server-side cookie sessions; SCUT spec uses JWT. JWT is the right choice for API-first systems because it enables stateless verification - agents hitting the API directly do not need a cookie jar. The kanban's agent_tokens table already provides a per-agent bearer-token mechanism, which is closer to JWT thinking. Migrating kanban's auth to JWT adds a `JWT_SECRET` env var and replaces the sessions table lookup with token verification - a ~100-line change.

**Current SCUT code vs. SCUT spec:**

The SCUT server code is approximately "Phase 0.5": it has the 4-table schema and routes for threads/messages/replicants/runs, but not the project hierarchy, auth middleware, checklist support, or SSE. The spec is the aspirational full design. Option A would be building out the SCUT spec using the kanban's proven implementations as the starting point for each subsystem.

---

## Recommendation

**Option A: Absorb kanban into SCUT.**

Rationale: SCUT's spec is more correct for the stated goals (API-first, ACP connector, future SaaS/managed service). The project/board/column hierarchy and connector interface are architectural investments that will be needed regardless and are hard to retrofit later. The kanban's working code is the right implementation to port into SCUT's structure - it is not wasted work, it becomes the implementation of Phases 2-3 of the spec.

**Concrete execution path:**

1. **Adopt kanban's migration runner** into `packages/server/src/db/`. Replace the static `schema.sql` + `migrate.ts` with the numbered migration file pattern from kanban (`src/server/migrations/`).
2. **Implement the full spec schema** in SCUT via migrations (projects, users, boards, columns, threads, comments, checklists, checklist_items, replicants, runs, checkpoints, agent_tokens).
3. **Port `SseManager`** from `src/server/sse.ts` (kanban) into `packages/server/src/sse/SseManager.ts` (SCUT). This is a drop-in copy; it has no external dependencies.
4. **Port `BridgeStream`** from `src/server/bridge-stream.ts` into `packages/server/src/connectors/BridgeStream.ts` and wire it into a new `CopilotBridgeConnector` that implements `IReplicantConnector` using streaming (replacing the current webhook stub).
5. **Port `AcpSessionManager`** from `src/server/acp-session-manager.ts` into `packages/server/src/connectors/AcpConnector.ts`, adapting it to implement `IReplicantConnector`.
6. **Port checkpoint model** from kanban's `cards.ts` (createCheckpoint/listCheckpoints) into a new `packages/server/src/db/adapters/sqlite/checkpoints.ts` in SCUT.
7. **Port run-resume endpoint** into SCUT's `packages/server/src/routes/runs.ts`.
8. **Implement JWT auth** in SCUT per the spec (the spec is already fully designed; the kanban's auth module provides the bcrypt + session patterns to reference).
9. **Archive `raykao/copilot-bridge-kanban`** after the above ports are validated.

**What is discarded from kanban:**
- Cookie-based session auth (replaced by JWT)
- `card.type = 'work' | 'chat'` distinction (threads serve both roles in SCUT; a `metadata.type` convention can serve the same purpose if needed)
- Flat card list without hierarchy (replaced by project/board/column structure)
- Direct DB function calls from route handlers (replaced by repository pattern)

**What is discarded from SCUT current code:**
- `packages/server/src/connectors/CopilotBridgeConnector.ts` (webhook stub, replaced by streaming version ported from kanban)
- `packages/server/src/db/schema.sql` static schema (replaced by migration files)
- Vestigial `bobId` field names in `IReplicantConnector.ts`

---

## Open Questions

1. **Naming:** Keep SCUT vocabulary ("Thread", "Replicant", "Comment", "Moot") or adopt kanban vocabulary ("Card", "Agent", "Comment", "Board")? The spec says Thread and Replicant. The question is whether to expose those terms in the UI or map them to more familiar names.
2. **Checkpoints:** Are checkpoints (`git_ref + turn_index`) a first-class entity in the canonical spec, or a copilot-bridge-specific feature? If first-class, add a CheckpointRepository to the spec interface.
3. **Card type:** Is the `work` vs. `chat` card distinction meaningful in the unified model, or is it a UI-level filter on `metadata.type`?
4. **Auth migration order:** Should JWT auth be implemented before or after the schema migration? Doing auth first means SCUT has working auth when the hierarchy migration runs. Doing schema first means the hierarchy is testable via curl without auth.
5. **Parallel operation:** Is there a period where both repos need to stay live (existing kanban deployments, active copilot-bridge integrations), and if so, how long?
6. **Labels vs. metadata.labels:** The kanban uses a `card_labels` join table; SCUT spec uses `metadata.labels` (a JSON array). The join table is more queryable; `metadata.labels` is more flexible. Which is canonical?

---

## References

1. `eridanilabs/scut` spec: `/home/raykao/.copilot-bridge/workspaces/bill/workbench/scut/docs/spec/spec.md`
2. `eridanilabs/scut` live schema: `packages/server/src/db/schema.sql`
3. `eridanilabs/scut` connector interface: `packages/server/src/connectors/IReplicantConnector.ts`
4. `raykao/copilot-bridge-kanban` DB layer: `src/server/db.ts`
5. `raykao/copilot-bridge-kanban` card routes: `src/server/card-routes.ts`
6. `raykao/copilot-bridge-kanban` SSE: `src/server/sse.ts`
7. `raykao/copilot-bridge-kanban` bridge stream: `src/server/bridge-stream.ts`
8. `raykao/copilot-bridge-kanban` ACP manager: `src/server/acp-session-manager.ts`
9. `raykao/copilot-bridge-kanban` agent admin routes: `src/server/agent-admin-routes.ts`
