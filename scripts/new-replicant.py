#!/usr/bin/env python3
"""
new-replicant.py - Bootstrap a new replicant agent on eridanilabs/replicant-matrix.

What it does:
  1. Creates the replicant/NAME branch from main in replicant-matrix
  2. Fills in AGENTS.md REPLICANT IDENTITY block
  3. Writes REPLICANT.md identity doc
  4. Writes replicant.env (no secrets, safe to commit)
  5. Creates the workspace directory at ~/.copilot-bridge/workspaces/NAME
  6. Writes .env (secrets, gitignored, chmod 600)
  7. Creates the MySQL user on the Dolt server with correct grants
  8. Runs bd init --server to wire up shared Beads DB
  9. Updates metadata.json project_id to match server
  10. Pushes the branch and wires workspace git remote
  11. Prints the config.json channel snippet to add manually

Usage:
  python3 scripts/new-replicant.py NAME CHANNEL ROLE_DESCRIPTION

  NAME     - agent name (lowercase, e.g. "data", "forge")
  CHANNEL  - mattermost channel name (e.g. "scut-data")
  ROLE     - one-line role description (e.g. "Data pipeline and analytics agent")

Prerequisites:
  - git, gh CLI, bd, docker all available
  - Run from anywhere (uses absolute paths)
  - Dolt server running at 127.0.0.1:3307 (docker-compose up)
  - Set MYSQL_ROOT_PASSWORD env var or pass --root-password

Example:
  python3 scripts/new-replicant.py data scut-data "Data pipeline and analytics agent"
"""

import argparse
import os
import json
import secrets
import string
import subprocess
import sys
import textwrap
from pathlib import Path

WORKSPACE_BASE = Path("/home/raykao/.copilot-bridge/workspaces")
REPLICANT_MATRIX_REPO = "eridanilabs/replicant-matrix"
DOLT_CONTAINER = "copilot-bridge-dolt-1"
PROJECT_ID = "d4dd24e1-3236-4e0c-b8fa-ce40043acc86"
DOLT_DATABASE = "replicant"
DOLT_HOST = "127.0.0.1"
DOLT_PORT = 3307
BD_BIN = Path("/home/raykao/.local/bin/bd")


def run(cmd, check=True, capture=False, env=None):
    print(f"  $ {cmd}", flush=True)
    result = subprocess.run(
        cmd, shell=True, check=check,
        capture_output=capture, text=True,
        env={**os.environ, **(env or {})}
    )
    return result


def gen_password(length=32):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def dolt_sql(query):
    result = subprocess.run(
        f"docker exec {DOLT_CONTAINER} dolt sql -q \"{query}\"",
        shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Dolt SQL failed: {result.stderr.strip()}")
    return result.stdout.strip()


def create_db_user(name, password):
    print(f"\n[5] Creating MySQL user '{name}' on Dolt server...")
    dolt_sql(f"DROP USER IF EXISTS '{name}'@'%';")
    dolt_sql(f"CREATE USER '{name}'@'%' IDENTIFIED BY '{password}';")
    dolt_sql(
        f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX "
        f"ON {DOLT_DATABASE}.* TO '{name}'@'%';"
    )
    dolt_sql(f"GRANT SUPER ON *.* TO '{name}'@'%';")
    dolt_sql("FLUSH PRIVILEGES;")
    print(f"  OK - user '{name}'@'%' created with scoped grants + SUPER")


def init_beads(name, workspace):
    print(f"\n[6] Initialising Beads (server mode, database={DOLT_DATABASE})...")
    env = {
        "PATH": f"/home/raykao/.local/bin:{os.environ.get('PATH', '')}",
        "BEADS_DIR": str(workspace / ".beads"),
        "BEADS_ACTOR": name,
    }
    for line in (workspace / ".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

    run(
        f"{BD_BIN} init --server "
        f"--database {DOLT_DATABASE} "
        f"--prefix {name[:3].upper()} "
        f"--external "
        f'--destroy-token "DESTROY-{name}"',
        env=env
    )

    meta_path = workspace / ".beads" / "metadata.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["project_id"] = PROJECT_ID
        meta["dolt_server_user"] = name
        meta["backup"] = {"auto": False}
        meta["export"] = {"auto": False}
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        print(f"  OK - metadata.json project_id set to {PROJECT_ID}")
    else:
        print("  WARN: metadata.json not found after bd init - check manually")


def create_branch(name, role, channel, repo_root):
    print(f"\n[1] Creating branch replicant/{name} from main...")
    run(f"git -C {repo_root} fetch origin")
    run(f"git -C {repo_root} checkout -b replicant/{name} origin/main")

    print(f"\n[2] Writing REPLICANT.md...")
    replicant_md = textwrap.dedent(f"""\
        # {name.capitalize()} - {role}

        Human-readable companion to the REPLICANT IDENTITY block in AGENTS.md.
        This file is for documentation and diffing only - not loaded at runtime.

        **Agent**: {name}
        **Channel**: {channel}
        **Base**: `{REPLICANT_MATRIX_REPO}` branch `replicant/{name}`
        **Workspace**: `{WORKSPACE_BASE}/{name}`

        ## Role

        {role}

        ## Update Instructions

        To pull shared base updates from main:
          git rebase main

        Only AGENTS.md lines inside BEGIN/END REPLICANT IDENTITY and this file
        will ever conflict. Resolve by keeping {name}'s values.
    """)
    (repo_root / "REPLICANT.md").write_text(replicant_md)

    print(f"\n[3] Writing REPLICANT IDENTITY block in AGENTS.md...")
    agents_path = repo_root / "AGENTS.md"
    agents_content = agents_path.read_text()
    identity_block = textwrap.dedent(f"""\
        <!-- BEGIN REPLICANT IDENTITY -->
        **Agent**: {name}
        **Workspace**: `{WORKSPACE_BASE}/{name}`
        **Beads**:
          - `BEADS_DIR="{WORKSPACE_BASE}/{name}/.beads"`
          - `BEADS_ACTOR="{name}"`
        **Branch prefix**: `{name}/`
        **Worktree prefix**: `{name}-`
        **Session handoff key prefix**: `session-handoff-{name}-`
        **Channel**: {channel}
        **Base branch**: `replicant/{name}` in `{REPLICANT_MATRIX_REPO}`

        ## Role

        {role}

        ## Domain Focus

        TODO: fill in repos and layers this replicant owns.

        **Does NOT own**: TODO

        ## Active Task Queue

        (empty - update as tasks are assigned)
        <!-- END REPLICANT IDENTITY -->""")

    agents_content = agents_content.replace(
        "<!-- BEGIN REPLICANT IDENTITY -->\n<!-- END REPLICANT IDENTITY -->",
        identity_block
    )
    agents_path.write_text(agents_content)

    print(f"\n[4] Writing replicant.env (no secrets, safe to commit)...")
    replicant_env = textwrap.dedent(f"""\
        # {name} - runtime environment
        # BEADS_DOLT_PASSWORD is set in .env (gitignored, never committed)
        BEADS_DIR={WORKSPACE_BASE}/{name}/.beads
        BEADS_ACTOR={name}
        BEADS_DOLT_USER={name}
    """)
    (repo_root / "replicant.env").write_text(replicant_env)


def create_workspace(name, password):
    workspace = WORKSPACE_BASE / name
    print(f"\n[4b] Creating workspace at {workspace}...")
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "workbench").mkdir(exist_ok=True)

    dot_env = workspace / ".env"
    dot_env.write_text(textwrap.dedent(f"""\
        BEADS_DOLT_PASSWORD={password}
        BEADS_DOLT_USER={name}
        BEADS_DIR={workspace}/.beads
        BEADS_ACTOR={name}
    """))
    dot_env.chmod(0o600)
    print(f"  OK - .env written (chmod 600)")
    return workspace


def commit_and_push(repo_root, name):
    print(f"\n[7] Committing and pushing replicant/{name}...")
    run(f"git -C {repo_root} add REPLICANT.md AGENTS.md replicant.env scripts/")
    run(
        f'git -C {repo_root} commit -m '
        f'"chore({name}): bootstrap replicant/{name} branch\n\n'
        f'Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"'
    )
    run(f"git -C {repo_root} push -u origin replicant/{name}")
    run(f"git -C {repo_root} checkout main")


def wire_workspace(name, workspace):
    print(f"\n[8] Wiring workspace git to replicant-matrix replicant/{name}...")
    git_dir = workspace / ".git"
    if not git_dir.exists():
        run(f"git -C {workspace} init")
    run(
        f"git -C {workspace} remote add origin "
        f"https://github.com/{REPLICANT_MATRIX_REPO}.git || true",
        check=False
    )
    run(
        f"git -C {workspace} remote set-url origin "
        f"https://github.com/{REPLICANT_MATRIX_REPO}.git"
    )
    run(f"git -C {workspace} fetch origin")
    run(f"git -C {workspace} checkout --track origin/replicant/{name}")


def print_config_snippet(name, channel):
    snippet = {
        "platform": "mattermost",
        "name": channel,
        "bot": name,
        "workingDirectory": str(WORKSPACE_BASE / name),
        "model": "claude-sonnet-4.6",
        "agent": None,
        "triggerMode": "all",
        "threadedReplies": False,
        "verbose": False
    }
    print("\n" + "=" * 60)
    print("ACTION REQUIRED: Add this to config.json channels array,")
    print("then restart copilot-bridge:")
    print("=" * 60)
    print(json.dumps(snippet, indent=2))
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Bootstrap a new replicant agent")
    parser.add_argument("name", help="Agent name (lowercase, e.g. 'data')")
    parser.add_argument("channel", help="Mattermost channel name (e.g. 'scut-data')")
    parser.add_argument("role", help="One-line role description")
    parser.add_argument(
        "--skip-db", action="store_true",
        help="Skip DB user creation and bd init (re-run safety)"
    )
    args = parser.parse_args()

    name = args.name.lower()

    # Find repo root - script lives in scripts/ inside the repo
    repo_root = Path(__file__).parent.parent

    password = gen_password()

    print(f"\n=== Bootstrapping replicant: {name} ===\n")

    # 1-4: Branch + files in repo
    create_branch(name, args.role, args.channel, repo_root)

    # 4b: Workspace + .env
    workspace = create_workspace(name, password)

    if not args.skip_db:
        # 5: DB user
        create_db_user(name, password)
        # 6: Beads init
        init_beads(name, workspace)

    # 7: Commit + push branch
    commit_and_push(repo_root, name)

    # 8: Wire workspace to branch
    wire_workspace(name, workspace)

    print(f"\n[9] Done.")
    print(f"  Branch:     replicant/{name} on {REPLICANT_MATRIX_REPO}")
    print(f"  Workspace:  {workspace}")
    print(f"  DB user:    {name}@% on {DOLT_HOST}:{DOLT_PORT}")
    print(f"  .env:       {workspace}/.env (chmod 600)")

    print_config_snippet(name, args.channel)


if __name__ == "__main__":
    main()
