# Memory

> **DEPRECATED:** This file is no longer the primary memory store.  
> Use `bd remember` and `bd memories <keyword>` instead.  
> This file will not be updated going forward.

## Project Context

**Repo:** `raykao/copilot-bridge-kanban` — Kanban web app acting as ACP client for AI coding agents.  
**Location:** `/home/raykao/.copilot-bridge/workspaces/riker/workbench/copilot-bridge-kanban`  
**Ports:** Kanban 3000, Copilot ACP 3456, Bob ACP 4000  
**SQLite DB:** `workbench/copilot-bridge-kanban/data/kanban.db` (user: raykao/admin123)

## Environment Setup

- **Beads workspace:** `/home/raykao/.copilot-bridge/workspaces/riker/.beads/` (prefix: RKR)
- **Beads dolt:** `/home/raykao/.local/bin/dolt` — prepend to PATH: `PATH="/home/raykao/.local/bin:$PATH"`
- **Dev server:** `setsid bash -c 'npm run dev > /tmp/kanban-server.log 2>&1' &` with detach
- **Bob ACP:** `127.0.0.1:4000`; config at `/home/raykao/.copilot-bridge/workspaces/bob/config-acp-test.json`

## Build & Process Commands

- Dev: `npm run dev` (uses tsx with --env-file=.env)
- Build: `npm run build` (runs `tsc -p tsconfig.server.json && vite build`)
- Test: `npm test` (vitest, expected: 267 passed, 26 skipped)
- Find port 3000 PID: `lsof -ti:3000` — use explicit PID kill, wait 3s before restart

## ACP Protocol Facts

- ACP spec stable transport: **stdio only** (NDJSON); Streamable HTTP = draft; raw TCP = custom extension; WebSocket = NOT in spec
- No discovery mechanism — one endpoint = one agent; identity from config, not server
- `agentInfo` in `initialize` response is SHOULD (optional); `protocolVersion` + `agentCapabilities` are MUST
- `session/cancel` is notification (no `id` field); custom methods prefixed `_`
- `session/prompt` requires `ContentBlock[]` not plain string
- `agentCapabilities.sessionCapabilities.resume` (Copilot/bob) differs from spec's `agentCapabilities.loadSession`
- `cwd` in `session/new` MUST be absolute path per ACP spec
- **Agent identity** (`.github/agents/*.agent.md`, `AGENTS.md`): loaded from server startup directory
- **Multi-agent personalities require multi-process**: one `copilot --acp --port N` per agent

## Two ACP Backend Variants [2026-05-27]

**Variant A (`ghcp-cli`)**: Operator spawns `copilot --acp --port N` from persona dir; persona bound to spawn cwd's AGENTS.md; CBK MUST send `cwd` per session.  
**Variant B (`copilot-bridge-v2`)**: Long-running Node.js server using `@github/copilot-sdk`; each agent on its own TCP port; persona set per-session via `agent: <name>` field; bridge defaults workspace from `botCfg.workingDirectory`.

**Spawn cwd vs Session cwd** (ghcp-cli only):
- Spawn cwd: `.../workspaces/<name>` — reads AGENTS.md, bakes persona into system prompt
- Session cwd: `.../workspaces/<name>/workbench` — CBK sends as `session/new` cwd

**copilot-bridge v2 key internals** (`/tmp/copilot-bridge`):
- Config: `platforms.acp.{basePort, bind, agents: Record<name, AcpBotConfig>}`
- `workingDirectory = params.cwd ?? botCfg.workingDirectory ?? process.cwd()`
- Capabilities: `sessionCapabilities.resume`, `sessionCapabilities.close` (NO `loadSession`)
- NO HTTP catalog endpoint, NO `/v1/agents/cards`

## Session Continuation Priority (StandardAcpRunner.run)

1. `session/resume` if `caps.sessionCapabilities.resume` → silent reconnect
2. `session/load` if `caps.loadSession` → server replays history
3. `session/new` → fresh session, context lost

Timeouts: 30s for session ops (resume/load), 10m for prompt() to prevent hung sessions.

## Architecture Decisions

- `StandardAcpProvider` for all ACP agents (stdio/TCP); `CopilotBridgeProvider` for copilot-bridge WS protocol
- Provider `label` is canonical agent name — baked into constructor; PATCH rebuilds instance
- Duplicate agents fix: exclude DB agents whose `provider_id` in `registry.getAllHealth()`
- `ws_url` column kept (SQLite can't DROP); removed from TypeScript types/queries
- No `runs` table — ACP session state on `cards.session_id`; dropped in migration 015
- CWD resolution priority: `card.workspace_subdir` → `provider.defaultCwd` → `os.homedir()`
- URL parser fix: strip protocol prefix via regex `/^[a-z]+:\/\//i` before splitting host:port
- `workspace_path?.trim() || undefined` normalization prevents empty string from bypassing `os.homedir()` fallback
- Legacy `copilot-bridge` provider type marked **obsolete**; split into `ghcp-cli` and `copilot-bridge-v2` backends

## Provider Settings UI [2026-05-26]

`AddProviderForm` refactored to `ProviderForm` supporting `mode: 'add' | 'edit'`:
- Type field **disabled** in edit mode
- API Key blank = keep existing (sent as `undefined`); non-blank = update
- Form uses `key={editingProvider.id}` to force re-mount when switching providers
- Backend PATCH at `provider-admin-routes.ts:91` supports all fields
- `AdminProviderUpdate` type in `client.ts` (lines 49-56); `api.admin.providers.update(id, body)` added

## Permission Approval Flow

- Server emits `run.awaiting` SSE with `request_id`, `tool`, `kind`, `summary`, `details`
- `useCardEvents` captures into `awaitingPermission` state (including `requestId`)
- `StreamingMessage` renders `PermissionApproval` when `awaitingPermission && cardId`
- User clicks → `api.runs.resume(cardId, runId, decision, requestId)` → POST `/api/cards/:id/resume`

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/server/providers/standard-acp.ts` | StandardAcpRunner; `withTimeout()` L35; `run()` L169; `isPrompting` flag gates session updates during history replay |
| `src/server/providers/build.ts` | Factory routing transport to provider; URL protocol stripping; workspace_path normalization |
| `src/server/providers/registry.ts` | `nameIndex` map; 60s health monitor |
| `src/server/card-routes.ts` | Exports `buildSessionCallbacks`; `resolveAndDispatch()` |
| `src/server/provider-admin-routes.ts` | Provider CRUD; PATCH at L91; rebuilds on label/transport/url change |
| `src/client/pages/SettingsPage.tsx` | `ProviderRow`, `ProviderForm` (add/edit), `SettingsPage` |
| `src/client/api/client.ts` | `AdminProviderCreate`/`AdminProviderUpdate` types; `api.admin.providers` methods |
| `src/client/components/chat/ChatView.tsx` | L241: tool output fix; L259: passes `cardId` to StreamingMessage |
| `src/client/components/card/StreamingMessage.tsx` | `PermissionApproval` component L18; `cardId` prop required |
| `src/client/hooks/useCardEvents.ts` | SSE handler; captures `requestId` from `run.awaiting` |
| `workbench/copilot-bridge-kanban/docs/acp-provider-architecture.md` | CBK ACP architecture doc — dirty, not committed as of 2026-05-27 |
| `/tmp/copilot-bridge/docs/acp-server.md` | copilot-bridge v2 ACP server doc; 341 lines; branch `docs/acp-server-v2` pushed to raykao/copilot-bridge fork |

## Pending Work [2026-05-27]

- [ ] Open PR: `cd /tmp/copilot-bridge && gh pr create --base main --head docs/acp-server-v2 --title "docs: add ACP server (v2) reference"`
- [ ] Commit dirty CBK doc: `git add docs/acp-provider-architecture.md && git commit -m "docs(acp): split acp provider into ghcp-cli and copilot-bridge-v2 backends"`
- [ ] Update Beads epic `RKR-fqz` children (.1–.4) with backend-aware notes
- [ ] Consider filing `RKR-fqz.5` (permission approval policy) and a daedalus future-provider issue

## Known Issues

- 26 tests remain skipped (bridge streaming integration, A2A push callbacks, `cards.test.ts > runs`)