# UI-TRUTH-01C — Failure, stale, retry, and drill-down states

**Task:** `UI-TRUTH-01C`  
**Canonical title:** **Failure, stale, retry, and drill-down states**  
**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Depends:** UI-TRUTH-01B COMPLETE — PROVEN_V1 · Current Truth Control Center V1 COMPLETE — PROVEN_CURRENT  
**Status:** **IN IMPLEMENTATION** (owner UNPAUSE)

---

## Owner decision — 2026-07-17 (binding)

```text
UI-TRUTH-01C = UNPAUSE

G1 LIVE BADGE = RENAME
G2 CRITICAL = HIDE
G3 MODULES HEALTH = KEEP
G4 DB TRUTH = CONSUME (existing diagnostics contract only)

IMPLEMENTARE UI-TRUTH-01C = GO
```

**Keep intact:** UI-TRUTH-01B banner mapping · `/modules` poller · Control Center · Wave 7 · UTF-8/G13  
**Forbidden:** backend contract changes · new alerts API · shell redesign · Control Center ownership rewrite

---

## Scope (DoD)

| Area | Requirement |
|------|-------------|
| Manual refresh | `Reverifică starea` — loading, no duplicate concurrent refresh |
| Stale UX | `Stare învechită` + last check; not positive-as-current |
| Retry | `Reîncearcă` on failure; last-known clearly labeled |
| Drill-down | `RuntimeStatusDetails` — env, backend, DB, freshness, diagnostics access |
| Diagnostics | Authorized detail / clear 403 Romanian message; no forbidden poll loop |
| Dashboard | Rename misleading `Live` → business-data label |
| Shell | Hide mock `2 critical` when no real alert source |

---

## Prior pause record

Previously PAUSED after 01B; resumed after Control Center V1 (`d845670`). Deferred findings G1/G2/G4 are now in scope; G3 remains KEEP.
