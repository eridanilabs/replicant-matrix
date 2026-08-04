# SCUT Phase 2 -- Gaps, Rename Audit, and Work Breakdown

**Status:** Complete
**Date:** 2025-07-22
**Question:** What naming violations exist (Bob vs. Replicant), what P2 deliverables are missing vs. already built, and what is the complete P2 work breakdown?
**Informs:** P2 implementation planning and task scoping for the SCUT project.

---

## Summary

The P1 backend that was merged (PR #5) implemented only the agent-integration backbone (bobs/threads/messages/runs) -- NOT the full P1 kanban hierarchy from the spec (projects, boards, columns, users, checklists). The UI is 100% mock-based with zero real API calls. All code uses "Bob" naming where the spec exclusively uses "Replicant". P2 therefore has three distinct work streams: (1) complete the P1 kanban schema and API that was skipped, (2) do the Bob->Replicant rename throughout, and (3) add the actual P2 agent-dispatch behaviors. The rename should be done as part of P2 in a single schema migration that handles all structural changes at once.

---

## Context

PR #5 was described as "P1 backend." On inspection it delivered a partial agent-integration layer rather than the full P1 Kanban platform. The React UI was scaffolded with mock data only. The spec (section 13) defines strict phase boundaries; the current code satisfies approximately 20% of Phase 1 and 60% of the Phase 2 infrastructure (correctly shaped behaviors, wrong names).

---

## What We Know

### Spec naming

The spec uses "Replicant" exclusively as the code-level name for registered agent connectors. Specific instances (line 98): "A registered agent connector instance. Named after Bobiverse replicants." The word "Bob" never appears as a symbol name, table name, or route segment in the spec. The spec names are:

- Table: `replicants`
- FK column on threads: `assignee_id` (with `assignee_type = 'replicant'`)
- FK column on runs: `replicant_id`
- Interface: `IReplicantConnector`
- Type: `ReplicantStatus`
- Class: `CopilotBridgeConnector`
- Routes: `/api/replicants`

### Current schema vs. spec schema

The actual deployed schema (`packages/server/src/db/schema.sql`) has only 4 tables: `bobs`, `threads`, `messages`, `runs`. The spec's target schema for Phase 1 + 2 has 11 tables: `projects`, `users`, `boards`, `columns`, `threads` (different shape), `comments` (not `messages`), `checklists`, `checklist_items`, `replicants`, `runs`.

Structural differences in the tables that do exist:

| Column | Actual (current) | Spec |
|--------|-----------------|------|
| threads.project_id | MISSING | TEXT NOT NULL REFERENCES projects(id) |
| threads.parent_id | MISSING | TEXT REFERENCES threads(id) |
| threads.assignee_type | MISSING | TEXT ('user' / 'replicant' / null) |
| threads.assignee_id | MISSING | TEXT |
| threads.bob_id | EXISTS (wrong) | Does not exist |
| threads.status values | idea/refining/ready/in_progress/blocked/done/archived | todo/in_progress/blocked/done/archived |
| messages table | EXISTS | Should be `comments` with author_type/author_id instead of author/author_id |
| messages.author | 'human'/'bob'/'system' string | author_type: 'user'/'replicant'/'system' |
| runs.bob_id | EXISTS (wrong) | Should be `replicant_id` |
| bobs table | EXISTS (wrong name) | Should be `replicants` with `metadata` column added |

### What was built in P1 (PR #5)

Built:
- `bobs` table, `BobRepo.ts`, `/api/bobs` CRUD routes (GET list, GET one, POST, PATCH, DELETE)
- `threads` table, `ThreadRepo.ts`, `/api/threads` CRUD routes (simplified -- no project scope)
- `messages` table, `MessageRepo.ts`, `/api/threads/:id/messages` routes (GET, POST -- no auth, no dispatch)
- `runs` table, `RunRepo.ts`, `/api/threads/:id/runs` (GET list, POST manual dispatch), `/api/runs/:id` (GET, PATCH)
- `POST /api/internal/runs/:id/result` callback endpoint
- `IBobConnector` interface (wrong name, wrong shape)
- `CopilotBridgeBob` class (wrong name, correct behavior)
- `ConnectorRegistry` (correct behavior, wrong symbol names)
- `bootstrap/connectors.ts` (correct behavior, wrong names)
- `seed-bob.ts` (correct behavior, wrong names)
- UI components: `BobsPage`, `BobSelector`, `BobBadge`, `BobStatusIndicator`, `useBobsStore`
- UI: Run history panel in `ThreadDetailPage`
- UI: All mock data wiring

NOT built (from P1 spec deliverables, sections 11.1 through 11.9):
- `projects` table and `/api/projects` routes
- `boards` table and `/api/boards`, `/api/projects/:id/boards` routes
- `columns` table and `/api/columns`, `/api/boards/:id/columns` routes, filter_rule evaluation
- `users` table and `/api/auth/*`, `/api/users` routes
- `checklists` table and `/api/threads/:id/checklists` routes
- `checklist_items` table and `/api/checklists/:id/items`, `/api/checklist-items/:id/promote` routes
- JWT middleware and protected route enforcement
- `IRepository` interface pattern (spec section 9.3 -- all DB access is flat function calls today)
- `SQLiteRepository` class wrapping all adapters
- Real HTTP API client in the UI (all calls go through `mockFetch`)
- OpenAPI spec at `/api/docs` and `docs/api/openapi.yaml`
- Thread scoped to a project (`GET /api/projects/:id/threads`)
- Thread comments via `POST /api/threads/:id/comments` with auto-dispatch (not via messages endpoint)

---

## What We Don't Know

- Whether any of the current `bobs`/`threads`/`messages`/`runs` tables have production data that must survive migration, or whether a clean schema drop-and-recreate is acceptable.
- Whether the simplified thread status set (current: idea/refining/ready/in_progress/blocked/done/archived) was intentional divergence from the spec (todo/in_progress/blocked/done/archived) or an accident.
- Whether the `DmSession`/`DmMessage` types in `ui/src/api/types.ts` and `MessagesPage` are in-scope for SCUT or belong to a different feature.

---

## 1. Naming Audit

### Server: Files to rename

| Current file | Correct file | Why |
|---|---|---|
| `packages/server/src/db/BobRepo.ts` | `ReplicantRepo.ts` | Entity rename |
| `packages/server/src/connectors/IBobConnector.ts` | `IReplicantConnector.ts` | Interface rename |
| `packages/server/src/connectors/CopilotBridgeBob.ts` | `CopilotBridgeConnector.ts` | Class rename |
| `packages/server/src/routes/bobs.ts` | `replicants.ts` | Route rename |
| `packages/server/src/seed-bob.ts` | `seed-replicant.ts` | Script rename |

### Server: Symbols to rename

| File | Current name | Correct name | Change type |
|---|---|---|---|
| `BobRepo.ts` | `BobRow` | `ReplicantRow` | Rename type |
| `BobRepo.ts` | `listBobs()` | `listReplicants()` | Rename function |
| `BobRepo.ts` | `getBob()` | `getReplicant()` | Rename function |
| `BobRepo.ts` | `getBobByName()` | `getReplicantByName()` | Rename function |
| `BobRepo.ts` | `createBob()` | `createReplicant()` | Rename function |
| `BobRepo.ts` | `updateBob()` | `updateReplicant()` | Rename function |
| `BobRepo.ts` | `deleteBob()` | `deleteReplicant()` | Rename function |
| `IBobConnector.ts` | `IBobConnector` | `IReplicantConnector` | Rename interface |
| `IBobConnector.ts` | `BobStatus` | `ReplicantStatus` | Rename type |
| `IBobConnector.ts` | `Thread.bobId` | `Thread.replicantId` | Rename field |
| `IBobConnector.ts` | `Run.bobId` | `Run.replicantId` | Rename field |
| `CopilotBridgeBob.ts` | `CopilotBridgeBob` | `CopilotBridgeConnector` | Rename class |
| `CopilotBridgeBob.ts` | `CopilotBridgeBobConfig` | `CopilotBridgeConnectorConfig` | Rename type |
| `ConnectorRegistry.ts` | `IBobConnector` import | `IReplicantConnector` | Update import |
| `ConnectorRegistry.ts` | `registerConnector(bobId, ...)` | `registerConnector(replicantId, ...)` | Rename param |
| `ConnectorRegistry.ts` | `getConnector(bobId)` | `getConnector(replicantId)` | Rename param |
| `ConnectorRegistry.ts` | `removeConnector(bobId)` | `removeConnector(replicantId)` | Rename param |
| `routes/bobs.ts` | `bobRoutes` | `replicantRoutes` | Rename function |
| `routes/bobs.ts` | `GET /api/bobs` | `GET /api/replicants` | Rename route (breaking) |
| `routes/bobs.ts` | `GET /api/bobs/:id` | `GET /api/replicants/:id` | Rename route (breaking) |
| `routes/bobs.ts` | `POST /api/bobs` | `POST /api/replicants` | Rename route (breaking) |
| `routes/bobs.ts` | `PATCH /api/bobs/:id` | `PATCH /api/replicants/:id` | Rename route (breaking) |
| `routes/bobs.ts` | `DELETE /api/bobs/:id` | `DELETE /api/replicants/:id` | Rename route (breaking) |
| `routes/runs.ts` | `bobId` in request body | `replicantId` | Rename field (breaking) |
| `routes/internal.ts` | `author: 'bob'` | `author_type: 'replicant'` | Rename value (breaking) |
| `bootstrap/connectors.ts` | `listBobs()` import | `listReplicants()` | Update import |
| `bootstrap/connectors.ts` | `CopilotBridgeBob` import | `CopilotBridgeConnector` | Update import |
| `seed-bob.ts` | `BOB_NAME` env var | `REPLICANT_NAME` | Rename env var |
| `seed-bob.ts` | `BOB_WEBHOOK_URL` env var | `REPLICANT_WEBHOOK_URL` | Rename env var |
| `seed-bob.ts` | `BOB_CALLBACK_URL` env var | `REPLICANT_CALLBACK_URL` | Rename env var |
| `seed-bob.ts` | `BOB_SECRET` env var | `REPLICANT_SECRET` | Rename env var |
| `index.ts` | `import bobRoutes` | `import replicantRoutes` | Update import |

### DB: Tables and columns to rename (migration required)

| Current | Correct | Change type |
|---|---|---|
| Table `bobs` | `replicants` | Rename table (migration) |
| `threads.bob_id` column | `threads.replicant_id` (transitional; will become `assignee_id` in full schema) | Rename column (migration) |
| `runs.bob_id` column | `runs.replicant_id` | Rename column (migration) |
| `messages.author` value `'bob'` | `'replicant'` (and column rename to `author_type`) | Data migration + column rename |

### UI: Files to rename

| Current file | Correct file | Why |
|---|---|---|
| `packages/ui/src/api/bobs.ts` | `replicants.ts` | Module rename |
| `packages/ui/src/stores/bobs.ts` | `replicants.ts` | Store rename |
| `packages/ui/src/pages/BobsPage.tsx` | `ReplicantsPage.tsx` | Page rename |
| `packages/ui/src/components/bob/` (directory) | `replicant/` | Directory rename |
| `packages/ui/src/components/bob/BobSelector.tsx` | `replicant/ReplicantSelector.tsx` | Component rename |
| `packages/ui/src/components/bob/BobBadge.tsx` | `replicant/ReplicantBadge.tsx` | Component rename |
| `packages/ui/src/components/bob/BobStatusIndicator.tsx` | `replicant/ReplicantStatusIndicator.tsx` | Component rename |

### UI: Symbols to rename

| File | Current name | Correct name | Change type |
|---|---|---|---|
| `api/types.ts` | `Bob` interface | `Replicant` | Rename type |
| `api/types.ts` | `BobStatus` type | `ReplicantStatus` | Rename type |
| `api/types.ts` | `MessageAuthor` value `'bob'` | `'replicant'` | Rename value |
| `api/types.ts` | `Thread.bob_id` | `Thread.replicant_id` (transitional) | Rename field |
| `api/types.ts` | `Run.bob_id` | `Run.replicant_id` | Rename field |
| `api/bobs.ts` | `bobsApi` | `replicantsApi` | Rename export |
| `api/mock.ts` | `mockBobs` | `mockReplicants` | Rename const |
| `api/mock.ts` | `_bobs` | `_replicants` | Rename var |
| `api/mock.ts` | `getMockBobs()` | `getMockReplicants()` | Rename function |
| `api/mock.ts` | `createMockBob()` | `createMockReplicant()` | Rename function |
| `api/mock.ts` | all `bob_id` fields in mock data | `replicant_id` | Rename fields |
| `api/mock.ts` | `author: 'bob'` in messages | `author: 'replicant'` | Rename value |
| `stores/bobs.ts` | `useBobsStore` | `useReplicantsStore` | Rename store |
| `stores/bobs.ts` | `BobsState` | `ReplicantsState` | Rename type |
| `stores/threads.ts` | `bob_id` filter param | `replicant_id` | Rename param |
| `components/bob/BobSelector.tsx` | `BobSelector` | `ReplicantSelector` | Rename component |
| `components/bob/BobSelector.tsx` | `BobSelectorProps` | `ReplicantSelectorProps` | Rename type |
| `components/bob/BobBadge.tsx` | `BobBadge` | `ReplicantBadge` | Rename component |
| `components/bob/BobStatusIndicator.tsx` | `BobStatusIndicator` | `ReplicantStatusIndicator` | Rename component |
| `components/bob/BobStatusIndicator.tsx` | `BobStatusIndicatorProps` | `ReplicantStatusIndicatorProps` | Rename type |
| `pages/BobsPage.tsx` | `BobsPage` | `ReplicantsPage` | Rename component |
| `pages/BobsPage.tsx` | `AddReplicantDialog` | (already correct) | No change |
| `pages/ThreadDetailPage.tsx` | label "Assigned Bob" | "Assigned Replicant" | Rename label |
| `pages/ThreadDetailPage.tsx` | `useBobsStore` import | `useReplicantsStore` | Update import |
| `pages/ThreadDetailPage.tsx` | `BobSelector` import | `ReplicantSelector` | Update import |
| `pages/MootPage.tsx` | `Bob` type import | `Replicant` | Update import |
| `pages/MootPage.tsx` | `useBobsStore` import | `useReplicantsStore` | Update import |
| `pages/MootPage.tsx` | `bobMap` variable | `replicantMap` | Rename var |
| `App.tsx` | `BobsPage` import | `ReplicantsPage` | Update import |
| `App.tsx` | route `/bobs` | `/replicants` | Rename route |
| `components/layout/Sidebar.tsx` | `href: '/bobs'` | `href: '/replicants'` | Rename nav href |

### Spec naming consistency check

The spec is fully consistent on "Replicant" as the code-level name. The word "Bob" appears in the spec exactly once, as etymology: "Named after Bobiverse replicants" (line 98). No spec symbol, table, route, or interface uses "Bob." The code and spec are 100% divergent on naming.

---

## 2. P1 vs P2 Gap Analysis

### P2 Deliverables (spec lines 918-929)

**D1: `replicants` table + `IReplicantRepository` + SQLiteRepository module**
- Built in P1? Partially. The `bobs` table exists with the wrong name and is missing the `metadata` column. There is no `IReplicantRepository` interface. There is no `SQLiteRepository` class; the code uses flat function exports instead of the interface pattern the spec defines in section 9.
- Missing: rename table + add `metadata` column; create `IReplicantRepository` interface in `db/interfaces/`; wrap `BobRepo` functions in a class implementing that interface.

**D2: `runs` table + `IRunRepository` + SQLiteRepository module**
- Built in P1? Partially. The `runs` table exists. The `bob_id` column must become `replicant_id`. No `metadata` column. No `IRunRepository` interface. No `SQLiteRepository` class.
- Missing: migration to rename `bob_id` -> `replicant_id`, add `metadata`; create `IRunRepository` interface; wrap `RunRepo` in implementing class.

**D3: `IReplicantConnector` interface**
- Built in P1? Yes -- as `IBobConnector`. Needs rename and shape corrections (`bobId` -> `replicantId` in embedded types).
- Missing: rename only (no logic changes).

**D4: `CopilotBridgeConnector` (Phase 2 reference implementation)**
- Built in P1? Yes -- as `CopilotBridgeBob`. Behavior is correct. Spec config shape differs: spec uses `{ baseUrl, channelId, token }` (section 12); current code uses `{ webhookUrl, callbackUrl, secret }`. This is a config shape discrepancy beyond just naming.
- Missing: rename class; reconcile config shape to spec's `{ baseUrl, channelId, token }`.

**D5: Connector registry initialized at startup from `replicants` table**
- Built in P1? Yes -- `ConnectorRegistry.ts` + `bootstrap/connectors.ts`. Behavior is correct.
- Missing: update to use renamed symbols.

**D6: `POST /api/threads/:id/comments` -- auto-dispatch on comment post**
- Built in P1? No. The current route is `POST /api/threads/:threadId/messages` and has NO dispatch logic. It is a plain message insert.
- Missing entirely: (a) rename route from `/messages` to `/comments`; (b) add dispatch logic: if `thread.assignee_type === 'replicant'`, look up connector by `thread.assignee_id`, create Run, call `connector.dispatch`, return `{ comment, run }` from the endpoint; (c) thread must have `assignee_type`/`assignee_id` columns (P1 schema gap).

**D7: `POST /api/internal/runs/:id/result` callback endpoint**
- Built in P1? Yes. Endpoint exists in `routes/internal.ts`. The side-effect of creating a `messages` record uses `author: 'bob'` -- must become `author_type: 'replicant'` once the comments table is correct.
- Missing: update author value after schema migration.

**D8: Replicants API endpoints (11.10)**
- Built in P1? Partially. All CRUD routes exist at `/api/bobs`. Missing: rename routes; the `DELETE` route currently returns a 409 with message "bob has associated runs" -- message text must reference "replicant."
- Missing: rename routes and error messages only.

**D9: Runs API endpoints (11.11)**
- Built in P1? Partially. `GET /api/threads/:id/runs` and `POST /api/threads/:id/runs` exist. `DELETE /api/runs/:id` (cancel) is NOT built.
- Missing: `DELETE /api/runs/:id` -- must call `connector.cancel(runId)` and set run status to `cancelled`.

**D10: Seed script -- default Replicant**
- Built in P1? Yes -- as `seed-bob.ts`. Behavior is correct.
- Missing: rename script and env vars.

**D11: Moot UI -- Replicant assignee picker + run status badge in thread detail**
- Built in P1? Partially. `BobSelector` and run history panel exist in `ThreadDetailPage`. However, the thread model uses `bob_id` directly; the spec uses polymorphic `assignee_type` + `assignee_id`. The picker will need to handle `assignee_type = 'replicant'` not just a flat `replicant_id`.
- Also: ALL UI calls use `mockFetch`. Zero real API calls are wired. The UI must be connected to the real API server as part of P2.
- Missing: (a) real API HTTP client replacing `mockFetch`; (b) update Thread type and components to use `assignee_type`/`assignee_id`; (c) rename all Bob symbols; (d) after rename, the store and API modules connect to `/api/replicants`.

### P1 deliverables missed entirely (not P2, but blocking P2)

The following P1 deliverables are absent and are prerequisites for P2 (agent assignment requires a thread to be scoped to a project, and auto-dispatch requires comments not messages):

- Projects CRUD (`/api/projects`, `projects` table)
- Boards CRUD (`/api/boards`, `boards` table)
- Columns CRUD with filter_rule evaluation (`/api/columns`, `columns` table)
- Users + auth JWT middleware (`/api/auth/*`, `/api/users`, `users` table)
- Checklists + ChecklistItems (`checklists`, `checklist_items` tables)
- Thread scoped to project (`threads.project_id`, `GET /api/projects/:id/threads`)
- `comments` table (replacing `messages`) with `author_type`/`author_id` shape
- `IRepository` interface pattern (`db/interfaces/IRepository.ts`)
- Real HTTP fetch client in UI (replacing `mockFetch`)
- Protected route enforcement (JWT middleware applied to all non-public routes)

---

## 3. P2 Work Breakdown

Tasks are listed in dependency order. Each can be a separate PR unless noted.

---

### T1: Full schema migration (prerequisite for all other tasks)

**What changes:**
- `packages/server/src/db/schema.sql` -- replace entirely with spec's schema (section 6.2)
- `packages/server/src/db/db.ts` -- no change needed; already runs schema on init via `db.exec(schemaSql)`
- New migration file (or drop-and-recreate if no production data)

**New tables added:** `projects`, `users`, `boards`, `columns`, `checklists`, `checklist_items`, `replicants` (replacing `bobs`), `comments` (replacing `messages`)

**Tables modified:**
- `threads`: add `project_id`, `parent_id`, `assignee_type`, `assignee_id`; drop `bob_id`; update status enum values
- `runs`: rename `bob_id` -> `replicant_id`; add `metadata`
- `messages` -> `comments`: rename table, change `author`/`author_id` shape to `author_type`/`author_id`

**Dependencies:** None -- must be first.

---

### T2: Rename all server-side symbols (Bob -> Replicant)

**What changes:**
- Rename `BobRepo.ts` to `ReplicantRepo.ts`; rename all exported symbols per naming audit table above
- Rename `IBobConnector.ts` to `IReplicantConnector.ts`; rename interface and types
- Rename `CopilotBridgeBob.ts` to `CopilotBridgeConnector.ts`; rename class; reconcile config shape to `{ baseUrl, channelId, token }`
- Update `ConnectorRegistry.ts` to use renamed types
- Rename `routes/bobs.ts` to `routes/replicants.ts`; update all route paths to `/api/replicants`
- Update `bootstrap/connectors.ts` to use renamed imports
- Rename `seed-bob.ts` to `seed-replicant.ts`; rename all `BOB_*` env vars
- Update `index.ts` imports and registrations
- Update `routes/internal.ts`: change `author: 'bob'` to `author_type: 'replicant'`

**Dependencies:** T1 (schema must use new column/table names before code can reference them).

---

### T3: Implement `IRepository` interface pattern (spec section 9.3)

**What changes:**
- Create `packages/server/src/db/interfaces/IRepository.ts` with all sub-interfaces from spec section 9.1
- Create `packages/server/src/db/interfaces/types.ts` with input/output types
- Create `packages/server/src/db/adapters/sqlite/` directory
- Create `SQLiteRepository` class in `adapters/sqlite/index.ts` implementing `IRepository`; move logic from flat repo files into class methods
- Create `packages/server/src/db/index.ts` factory function `createRepository(driver): IRepository`
- Update `index.ts` to call `createRepository('sqlite')` and pass to Fastify via `fastify.decorate`
- Update all route handlers to access repo via `request.server.db.*` instead of importing flat functions

**Dependencies:** T1, T2.

---

### T4: P1 missing API routes -- Projects, Boards, Columns, Users, Auth

**What changes:**
- `packages/server/src/routes/auth.ts` -- register/login/me/patch-me/logout with JWT middleware
- `packages/server/src/routes/users.ts` -- GET list, GET by id
- `packages/server/src/routes/projects.ts` -- full CRUD per spec 11.3
- `packages/server/src/routes/boards.ts` -- full CRUD per spec 11.4
- `packages/server/src/routes/columns.ts` -- CRUD + filter_rule evaluation (`findByColumn` in IThreadRepository evaluates the rule at query time) per spec 11.5
- `packages/server/src/middleware/auth.ts` -- JWT decode middleware; attaches `request.user`
- Update `index.ts` to register all new route plugins
- Add JWT dep: `@fastify/jwt` or `jsonwebtoken`

**Thread route changes:**
- `GET /api/threads` becomes `GET /api/projects/:id/threads` (scoped to project)
- `POST /api/threads` becomes `POST /api/projects/:id/threads`
- Thread body now includes `assignee_type`/`assignee_id` (not `bobId`)
- Thread filter params become `status`, `assignee_type`, `assignee_id`, `labels`

**Dependencies:** T1, T2, T3.

---

### T5: P1 missing API routes -- Checklists and ChecklistItems

**What changes:**
- `packages/server/src/routes/checklists.ts` -- full CRUD per spec 11.8
- `packages/server/src/routes/checklist-items.ts` -- full CRUD + `POST /api/checklist-items/:id/promote` per spec 11.9
- `promote` endpoint creates a new Thread with `parent_id` pointing to the checklist's parent thread

**Dependencies:** T1, T2, T3, T4 (needs Thread scoped to project).

---

### T6: Rename comments route and add auto-dispatch

**What changes:**
- Rename `routes/messages.ts` to `routes/comments.ts`; rename route from `POST /api/threads/:threadId/messages` to `POST /api/threads/:id/comments`
- Change POST body from `{ author, authorId, content, runId }` to `{ content, metadata? }` -- `author_type` and `author_id` are set server-side from JWT (`author_type='user'`, `author_id=request.user.id`)
- Add dispatch logic to `POST /api/threads/:id/comments`:
  1. Insert comment record
  2. Fetch thread; check `thread.assignee_type === 'replicant'`
  3. If yes: look up connector via `getConnector(thread.assignee_id)`
  4. Create Run record (`status='created'`, `input=content`, `replicant_id=thread.assignee_id`)
  5. Call `connector.dispatch(run, thread)` fire-and-forget
  6. Update run status to `'queued'`
  7. Return `201 { comment, run }` (run is null if no replicant assigned)
- Add `DELETE /api/comments/:id` and `PATCH /api/comments/:id` per spec 11.7

**Interaction with existing `POST /api/threads/:id/runs` route:**
- The manual dispatch route (`POST /api/threads/:id/runs`) is kept as-is for operator/API-client use
- The auto-dispatch is additive -- triggered by comment post, not a replacement
- Both paths converge at `connector.dispatch(run, thread)`

**Dependencies:** T1, T2, T3, T4 (needs auth middleware for `request.user.id`).

---

### T7: Add `DELETE /api/runs/:id` (cancel)

**What changes:**
- Add to `routes/runs.ts`:
  ```
  DELETE /api/runs/:id
  ```
  - Fetch run; 404 if not found
  - If status is `completed`/`failed`/`cancelled`, return 409 ("run is not cancellable")
  - Look up connector via `getConnector(run.replicant_id)`; call `connector.cancel(run.id)` if connector exists
  - Set run status to `cancelled`, `completed_at` to now
  - Return 204

**Dependencies:** T1, T2.

---

### T8: Seed script updates

**What changes:**
- Rename `seed-bob.ts` to `seed-replicant.ts` (per T2)
- Add seed data for default Project, Board with 4 columns (todo/in_progress/blocked/done filter rules), and default admin User
- `package.json` script `seed` should run `seed-replicant.ts`

**Dependencies:** T1, T4 (needs projects/boards/columns/users tables).

---

### T9: UI -- Real HTTP client and rename

**What changes:**
- Replace `mockFetch` in `packages/ui/src/api/client.ts` with a real `apiFetch(path, options)` function that calls the Fastify server, attaches `Authorization: Bearer <token>` header from auth store, and throws `ApiError` on non-2xx
- Rename all `Bob`/`bob` symbols in UI per naming audit table above
- Update `api/bobs.ts` -> `api/replicants.ts` to call `GET /api/replicants`, `POST /api/replicants`, etc.
- Update `api/threads.ts` to call `GET /api/projects/:id/threads`, `POST /api/projects/:id/threads`
- Update `api/messages.ts` -> `api/comments.ts` to call `GET /api/threads/:id/comments`, `POST /api/threads/:id/comments`
- Update `api/runs.ts` to call `GET /api/threads/:id/runs`
- Add auth API module (`api/auth.ts`) calling `/api/auth/login`, `/api/auth/register`, `/api/auth/me`
- Add projects API module (`api/projects.ts`)
- Add boards/columns API modules

**UI type changes:**
- `Thread` type: replace `bob_id: string | null` with `assignee_type: 'user' | 'replicant' | null` and `assignee_id: string | null`
- `Run` type: replace `bob_id` with `replicant_id`
- `Message`/`Comment` type: replace `author: MessageAuthor` with `author_type: 'user' | 'replicant' | 'system'`
- `BobSelector` -> `ReplicantSelector`: accepts `Replicant[]`, sets `assignee_type='replicant'` on change

**Shape mismatch: current mock vs. server response:**

| Field | Mock shape | Server shape (after migration) |
|---|---|---|
| Thread assignee | `bob_id: string or null` | `assignee_type, assignee_id` |
| Run replicant ref | `bob_id: string` | `replicant_id: string` |
| Message author | `author: 'human'/'bob'/'system'` | `author_type: 'user'/'replicant'/'system'` |
| Thread scope | `project_id` field exists | `project_id` required, scoped route |
| Thread status values | includes 'idea'/'refining'/'ready' | 'todo'/'in_progress'/'blocked'/'done'/'archived' |

All of these must be reconciled when swapping from mock to real. The UI `ThreadStatus` type in `api/types.ts` includes status values (`idea`, `refining`, `ready`) that do not exist in the spec's `threads.status` enum -- this will break filter_rule column matching if not corrected.

**Dependencies:** T4, T6 (needs real routes to exist before wiring).

---

### T10: OpenAPI spec generation

**What changes:**
- Add `@fastify/swagger` and `@fastify/swagger-ui` to server deps
- Add JSON schema blocks to all route handlers (only partial schema blocks exist today on a few routes)
- Serve OpenAPI 3.1 at `/api/docs`
- Commit generated `docs/api/openapi.yaml`

**Dependencies:** T4, T5, T6, T7 (all routes must exist before generating spec).

---

## 4. Rename Scope

### Is this a breaking API change?

Yes. Every route under `/api/bobs` becomes `/api/replicants`. Every request body that includes `bobId` must become `replicantId`. Any external client (a copilot-bridge instance, a seed script, a CI tool) that has hardcoded `/api/bobs` or `{ bobId: ... }` will break.

There are no known external clients in this repo other than the SCUT UI (which uses mocks today). The callback endpoint (`/api/internal/runs/:id/result`) does not change.

### Minimum rename to align with spec

At minimum to call the code "P2-compliant":
1. Table `bobs` -> `replicants` (DB migration)
2. Routes `/api/bobs` -> `/api/replicants` (breaking)
3. Request field `bobId` -> `replicantId` in POST /api/threads/:id/runs (breaking)
4. Interface `IBobConnector` -> `IReplicantConnector` (internal, non-breaking to API clients)
5. Class `CopilotBridgeBob` -> `CopilotBridgeConnector` (internal)

Symbol renames (steps 4-5) are internal and non-breaking to API clients. Steps 1-3 are breaking.

### DB table rename: migration vs. alias

Options:

| Option | Pros | Cons |
|---|---|---|
| Migration: `ALTER TABLE bobs RENAME TO replicants` | Clean, spec-compliant, no dead code | Requires coordinated deploy (code + DB together) |
| View alias: create `replicants` view over `bobs` | Old code still works, can migrate gradually | View is read-only in SQLite without triggers; `INSERT/UPDATE/DELETE` break |
| Drop and recreate | Simple if no prod data | Loses any existing rows |

**Recommendation:** Since there is no production data (the server has never run in production against the spec schema -- the current schema is already a diverged P1 prototype), drop-and-recreate with the full spec schema in a single migration. This is simpler than incremental ALTER TABLEs and produces a clean starting state.

### Recommended approach: rename as part of P2

Do the rename as part of P2, not as a separate cleanup task. Rationale:
1. P2 requires a schema migration regardless (adding `project_id` to threads, renaming `messages` to `comments`, adding `projects`/`boards`/`columns`/`users` tables). Doing the `bobs` -> `replicants` rename in the same migration costs nothing extra.
2. The code rename (symbols only, T2 above) is a mechanical find-and-replace. It should be the first P2 PR after T1 so that all subsequent PRs use correct names from the start.
3. If the rename is deferred, every new P2 PR adds more technical debt under the wrong name.

**Recommended PR sequence:**
1. T1: Schema migration (new schema.sql, migration runner)
2. T2: Server symbol rename (no behavior change, just rename)
3. T3: IRepository interface pattern
4. T4 + T5: P1 missing routes (Auth, Projects, Boards, Columns, Users, Checklists)
5. T6: Comments route + auto-dispatch (the core P2 feature)
6. T7: Run cancel endpoint
7. T8: Seed script updates
8. T9: UI real API wiring + rename
9. T10: OpenAPI spec generation

---

## Open Questions

1. **Is there production data in the current `scut.db`?** If yes, an ALTER-based migration is needed instead of drop-and-recreate. If no, drop-and-recreate is simpler.

2. **CopilotBridgeConnector config shape discrepancy.** The spec says `{ baseUrl, channelId, token }` (section 12) but the current `CopilotBridgeBob` uses `{ webhookUrl, callbackUrl, secret }`. Which shape matches the actual copilot-bridge API? This must be resolved before T2 can be marked complete.

3. **Thread status values.** The current code uses `idea/refining/ready/in_progress/blocked/done/archived`. The spec's `threads` table uses `todo/in_progress/blocked/done/archived`. Are the extra values (`idea`, `refining`, `ready`) intentional? The mock data and `ThreadStatus` type in the UI both use them. They are also referenced in `filter_rule` column seed data. If they stay, the spec's schema must be updated; if they go, the mock data and UI type must be updated.

4. **DM / Messages feature.** The UI has a `MessagesPage`, `DmSession`, `DmMessage` types, and `/messages` routes. These are not in the SCUT spec at all. Are they part of SCUT or a separate feature sharing the same codebase?

5. **`T9` timing.** Should the UI be wired to the real API as a standalone P2 PR (T9), or should it be done incrementally as each API route group lands? Incremental wiring allows earlier end-to-end testing but increases PR complexity.

---

## References

1. SCUT spec: `/home/raykao/.copilot-bridge/workspaces/bill/workbench/scut/docs/spec/spec.md`
2. Server schema: `packages/server/src/db/schema.sql`
3. Server routes: `packages/server/src/routes/`
4. Server connectors: `packages/server/src/connectors/`
5. UI API layer: `packages/ui/src/api/`
6. UI stores: `packages/ui/src/stores/`
7. UI components: `packages/ui/src/components/bob/`, `packages/ui/src/pages/`
