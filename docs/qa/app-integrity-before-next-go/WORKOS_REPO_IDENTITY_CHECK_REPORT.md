# WorkOS Repo Identity Check Report

**Mode:** READ-ONLY  
**Date:** 2026-07-31  
**Auditor:** Cursor agent (integrity GO Step 1→2)

---

## Mini decision

| Field | Verdict |
|-------|---------|
| Canonical active repo | **`C:\w\psiso`** |
| Stale / do-not-use for audit | **`C:\Users\offic\workos_app_vs`** |
| Same remote? | **Yes** — `https://github.com/office952/workos-vscode.git` |
| Integrity audit target | **Only `C:\w\psiso`** |

---

## Candidate A — `C:\w\psiso`

| Signal | Value |
|--------|-------|
| `git rev-parse --show-toplevel` | `C:/w/psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD short | `a1c28854` |
| HEAD full | `a1c28854dbeee553c8420c4639c8145ebe9d9230` |
| Tip subject | Merge pull request #37 — scoped-B for FIX-DEC009-MAT-02 / 92401 / 13 |
| Tip date | 2026-07-31 |
| Detached? | **No** |
| Live stack signals | `.workos-dev-detached.json` + `.workos-dev-logs` (started 2026-07-31 23:08) |
| Core folders | `backend`, `frontend`, `docs`, `exports`, `.github` present |
| Dirty | Employee lifecycle WIP (5 files) + untracked capacity-batch-19..20b QA docs |

---

## Candidate B — `C:\Users\offic\workos_app_vs`

| Signal | Value |
|--------|-------|
| `git rev-parse --show-toplevel` | `C:/Users/offic/workos_app_vs` |
| Branch | **Detached HEAD** (`## HEAD (no branch)`) |
| HEAD short | `82a713e0` |
| Tip date | 2026-07-13 — “Fix dev stack backend job error handling” |
| Live stack signals | Absent |
| Worktree note | Git lists `feat/capacity-batch-20d-scoped-b-92401` as checked out at **`C:/w/psiso`** |
| Dirty | Only `?? .compound-engineering/config.local.yaml` |
| Character | Stale detached checkout / archive-adjacent (zips, tmp build logs, `_archived_local_exports`) |

---

## Proof they are the same product remote

- Identical `origin` URL on both paths.
- Shared branch/worktree metadata across the two checkouts.
- Active feature tip lives only on `C:\w\psiso`.

---

## Stamp

**PASS** — Canonical active WorkOS repo confirmed as `C:\w\psiso`. Do not use `workos_app_vs` for further audits or Owner GOs.
