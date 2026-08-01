# Track B — Remaining QA Pack Classification

**Date:** 2026-08-01  
**Mode:** Classify only · no delete · no commit this track

---

## Classification matrix

| Item | Class | Recommendation |
|------|-------|----------------|
| `docs/qa/app-integrity-before-next-go/*.md` (reports, chapters) | Valuable integrity audit pack | **Commit separately** (docs-only), exclude `_tmp_*` |
| `docs/qa/app-integrity-before-next-go/_tmp_*.txt` | Ephemeral CI/preflight logs | **Delete only with Owner approval** |
| `docs/qa/exact-state-before-next-go/*` | Exact-state multi-track discovery | **Commit separately** (docs-only), same commit as integrity **or** adjacent |
| `docs/qa/push-92401-acceptance-hygiene/*` | Push hygiene report (post-push) | **Commit separately** with integrity/exact-state pack |
| `docs/qa/capacity-batch-19/` … `20b/` (partial) | Partial local mirrors; handoff often canonical | **Keep local** / leave untracked **or** separate docs commit if Owner wants in-repo mirrors |
| `docs/qa/operator-review-92401/_before_envelope_sha.txt` | Ephemeral RO hash | **Delete only with Owner approval** |
| `docs/qa/operator-review-92401/_tmp_task_list.txt` | Ephemeral | **Delete only with Owner approval** |
| `docs/qa/operator-review-92401/_tmp_task_rich.json` | Ephemeral | **Delete only with Owner approval** |
| `docs/qa/multitask-next-go/` (this pack) | Current planning GO | **Commit with** integrity/exact-state hygiene commit |
| Committed `docs/qa/operator-review-92401/*.md` (no `_tmp`) | Already in `e8ea40a0` | **Ignore** (done) |
| Suspicious product dirty | **None** | — |

---

## Recommended packaging (next docs commit)

**Include:**  
`app-integrity-before-next-go/` (md only) + `exact-state-before-next-go/` + `push-92401-acceptance-hygiene/` + `multitask-next-go/`

**Exclude:** all `_tmp*` / `_before*` · capacity-19..20b unless Owner explicitly wants them

**Capacity partials:** leave untracked unless Owner asks to land mirrors.

---

## Verdict

**PASS WITH WARNINGS** — clear commit vs delete vs leave-local map; no suspicious product dirt.
