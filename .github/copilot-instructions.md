# eridanilabs Engineering Conventions

This file provides shared conventions for all work in the **eridanilabs** GitHub organization.

## Repository Overview

| Repo | Purpose | Primary agent |
|------|---------|---------------|
| `eridanilabs/eridanilabs.github.io` | Public Hugo site (www.eridanilabs.io) | bill (hugo-dev) |
| Other org repos | Lab projects, tools | bill (implement) |

## Git Conventions

- **Commit format**: [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` new features
  - `fix:` bug fixes
  - `docs:` documentation changes
  - `style:` formatting, no logic change
  - `refactor:` code restructuring without behavior change
  - `chore:` maintenance (deps, config, tooling)
- **Scope**: Use the component or area, e.g. `feat(site):`, `fix(layout):`, `docs(content):`
- **No em dashes** in commit messages or any written artifacts - use hyphens, colons, or rephrase
- **Every commit** must include `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`

## Hugo Site (eridanilabs.github.io)

- Never modify files inside `themes/` - override in `layouts/`
- `hugo --minify` must exit 0 before any push to main
- GitHub Actions handles deploy to GitHub Pages on push to main
- Use `{{< ref >}}` and `{{< relref >}}` for internal links, never hardcoded paths

## Branch Naming

Agent-driven branches use the prefix `bill/`:
- `bill/feat/<slug>` for new features
- `bill/fix/<slug>` for bug fixes
- `bill/docs/<slug>` for documentation

## Pull Requests

- PR title follows Conventional Commits format
- PR body summarizes: what changed, why, how to verify
- All PRs should pass CI before merge
- Non-trivial PRs should have a review pass before merge

## Writing Style (all artifacts)

- No em dashes (--), en dashes, curly quotes, or non-ASCII punctuation
- Plain ASCII only in all markdown, commit messages, and code comments
- Be direct and specific - name the thing, not the category
- Avoid hollow adjectives ("powerful", "robust", "seamless") without evidence
