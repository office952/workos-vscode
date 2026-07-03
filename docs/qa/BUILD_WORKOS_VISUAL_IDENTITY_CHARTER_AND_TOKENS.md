# BUILD: WorkOS Visual Identity Charter + UI Tokens

**Date:** 2026-06-12  
**Status:** **PASS — document-only (uncommitted)**  
**Branch:** `local/integration-pr4-plus-svg-path` @ `3ad06a3`

---

## 1. Purpose

Create the **foundation documentation** for future WorkOS visual polish — visual identity charter, UI token draft, semantic status map, component standardization plan, and phased roadmap.

**No runtime implementation** in this build.

---

## 2. Context

Diagnostic conclusion (Figma vs WorkOS):

- Figma/Lovable are **not** a rewrite mandate
- WorkOS already has an **industrial dark ERP** direction
- Real problem: fragmentation between shadcn CSS vars (`index.css`) and operational hex values inline in pages
- Strategy: formalize `--wo-*` layer + incremental module rollout (shell last)

---

## 3. Scope

### Included

| Item | Path |
|------|------|
| Visual Identity Charter | `docs/design/WORKOS_VISUAL_IDENTITY_CHARTER.md` |
| UI Tokens Draft | `docs/design/WORKOS_UI_TOKENS_DRAFT.md` |
| Semantic Status Map | `docs/design/WORKOS_SEMANTIC_STATUS_MAP.md` |
| Component Standardization Plan | `docs/design/WORKOS_COMPONENT_STANDARDIZATION_PLAN.md` |
| Visual Roadmap | `docs/design/WORKOS_VISUAL_ROADMAP.md` |
| This QA doc | `docs/qa/BUILD_WORKOS_VISUAL_IDENTITY_CHARTER_AND_TOKENS.md` |

### Explicitly excluded

| Area | Action |
|------|--------|
| Runtime / CSS | **No changes** — `--wo-*` not added to `index.css` |
| React components | **No changes** |
| App shell | **No changes** |
| Frontend logic | **No changes** |
| Backend | **No changes** |
| Database | **No changes** |
| Seed | **Not run** |
| Migrations | **Not run** |
| Git commit | **Not performed** (per task instruction) |

---

## 4. Files created

```
docs/design/WORKOS_VISUAL_IDENTITY_CHARTER.md
docs/design/WORKOS_UI_TOKENS_DRAFT.md
docs/design/WORKOS_SEMANTIC_STATUS_MAP.md
docs/design/WORKOS_COMPONENT_STANDARDIZATION_PLAN.md
docs/design/WORKOS_VISUAL_ROADMAP.md
docs/qa/BUILD_WORKOS_VISUAL_IDENTITY_CHARTER_AND_TOKENS.md
```

**Files modified:** none  
**Files deleted:** none

---

## 5. Commands run

### Precheck (TASK 0)

```powershell
git branch --show-current   # local/integration-pr4-plus-svg-path
git rev-parse --short HEAD  # 3ad06a3
git status --short          # ?? docs/mockups/ (pre-existing untracked)
git log --oneline -10
```

Precheck **PASS**:

- Branch matches expected
- HEAD matches `3ad06a3`
- No uncommitted modifications to tracked files; only pre-existing untracked `docs/mockups/`

### Validation

No backend pytest, frontend Vitest, or E2E — not applicable for document-only scope.

---

## 6. Key decisions captured in docs

| Decision | Recommendation |
|----------|----------------|
| Visual direction | Keep industrial dark ERP; no third visual system |
| Token layer | `--wo-*` documented; maps from existing hex in Quotes/Orders/Operator |
| Figma role | Reference for Plăți angajați; not 1:1 copy |
| Badge shape | Rectangular 6px (`--wo-radius-sm`) — owner sign-off Phase 0 |
| Tabs | Underline default; segmented only where justified |
| Shell | Phase 4 last |
| `--wo-status-danger` | TBD — owner must pick exact red |
| Module order Phase 3 | Plăți → Quotes → Orders → Execution → Operator/Tablet → Pricing |

---

## 7. Boundary

This build **must not** be interpreted as authorization to:

- Change CostEngine, pricing logic, or status lifecycle
- Resync Figma/Lovable into production UI wholesale
- Modify `index.css` or Tailwind config
- Refactor App shell or sidebar

Next work requires a **separate build**: Phase 2 Shared Primitives + CSS Tokens.

---

## 8. PASS / FAIL

| Gate | Result |
|------|--------|
| Document-only scope | **PASS** |
| All 6 docs created | **PASS** |
| No runtime diff | **PASS** |
| Precheck branch/HEAD | **PASS** |
| Commit | **N/A** (explicitly not requested) |

**Overall: PASS**

---

## 9. Next recommended build

**WorkOS Visual Phase 2 — Shared Primitives + CSS Tokens**

1. Owner Phase 0 sign-off (badge, danger red, module priority)
2. Add `--wo-*` to CSS + Tailwind
3. Implement StatusBadge, MetricCard, SourceBadge, EmptyState
4. Pilot one module (Plăți angajați or Quotes)
5. Targeted Vitest; document in new `BUILD_*` QA file

---

*Build log — document-only. No production behavior changed.*
