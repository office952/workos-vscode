# UI-TRUTH-01C — Scope audit and owner gates

**Task:** `UI-TRUTH-01C`  
**Canonical title:** **Failure, stale, retry, and drill-down states**  
**Type:** Planning / owner decision only — **no implementation**  
**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verified HEAD (at audit):** `5cb5aa6` (UI-TRUTH-01B CORE PASS)  
**Verdict (planning):** `UI_TRUTH_01C_SCOPE_CONFLICT` documented; owner chose pause  
**Status:** **PAUSED** — not cancelled

---

## Owner decision — 2026-07-17 (binding)

```text
UI-TRUTH-01C = KEEP PAUSED

G1 LIVE BADGE = RENAME — deferred
G2 CRITICAL = HIDE — deferred
G3 MODULES HEALTH = KEEP
G4 DB TRUTH = DEFER

DOCS-ONLY COMMIT = DA
IMPLEMENTARE UI-TRUTH-01C = STOP
```

**Dependency:** UI-TRUTH-01B **COMPLETE — PROVEN_V1** (preserved).  
**Implementation authorized:** **NO**.

**Resume condition:** Owner explicitly reprioritizes UI-TRUTH-01C **after** the Current Truth Control Center build (`/modules` + `/governance` present-truth work) completes or is paused by owner.

**New priority (separate):** `CURRENT_TRUTH_CONTROL_CENTER_AUDIT = ACTIVE` — audit-first; no implementation until owner reviews.

---

## 1. Canonical definition (preserved)

| Field | Value |
|-------|--------|
| Exact title | **Failure, stale, retry, and drill-down states** |
| Status | **PAUSED** |
| Depends | UI-TRUTH-01B COMPLETE — PROVEN_V1 |
| Existing DoD | Manual refresh; stale UX; diagnostics-gated DB segment; unauthorized message; `RuntimeStatusDetails.tsx`; tests timeout/retry/403/stale |
| Planned files | `RuntimeStatusDetails.tsx` (new), `EnvironmentBanner.tsx` (extend) — not started |
| Backend | No public-health contract change required for CONSUME path |
| Authority | `implementation_breakdown.json` · `health_contract_matrix.json` |

### Scope conflict (preserved for resume)

| Track | Content |
|-------|---------|
| Canonical 01C | Banner failure / stale / retry / diagnostics drill-down |
| Observed residual pack | Dashboard `Live`; shell mock `2 critical`; modules poller share; DB diagnostics |

Owner deferred residual gates (G1/G2/G4) and kept G3=KEEP. Full option analysis remains in prior revision of this plan and worklog.

---

## 2. Deferred findings (do not discard)

| Finding | Classification | Deferred action |
|---------|----------------|-----------------|
| Dashboard green **Live** | MISLEADING vs banner | G1=RENAME deferred |
| AppShell **`2 critical`** | MOCK | G2=HIDE deferred |
| `/modules` dual health poller | DUPLICATE poller, compatible today | G3=KEEP |
| DB neverificată / diagnostics | CORRECT public redaction; CONSUME later | G4=DEFER |

---

## 3. Recommended resume package (when unpaused)

Prior recommendation (not authorized now):

`UNPAUSE` · `G1=RENAME` · `G2=HIDE` · `G3=KEEP` · `G4=CONSUME`

Plus canonical drill-down DoD.

---

## 4. Explicit exclusions while paused

- No EnvironmentBanner rewrite beyond 01B  
- No PostJobTruth / Wave 7 / UTF-8 reopen  
- No Current Truth Control Center implementation inside this task ID  

---

## 5. Owner decision pack (resolved for pause)

```text
UI-TRUTH-01C = KEEP PAUSED
G1 LIVE BADGE = RENAME — deferred
G2 CRITICAL = HIDE — deferred
G3 MODULES HEALTH = KEEP
G4 DB TRUTH = DEFER
DOCS-ONLY COMMIT = DA
IMPLEMENTARE = STOP
```
