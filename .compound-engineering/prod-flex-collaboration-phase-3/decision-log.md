# PROD-FLEX-COLLABORATION-PHASE-3 — Owner Decision Log

**Task:** PROD-FLEX-COLLABORATION-PHASE-3-INTEGRATED-OPERATOR-MOBILE-V2-PLAN  
**Date:** 2026-07-16  
**Status:** **PHASE 3 PLAN READY FOR OWNER REVIEW**  
**Starting HEAD:** `d29e047`  
**Plan:** `.compound-engineering/prod-flex-collaboration-phase-3/plan.md`

---

## Already affirmed (planning input)

| Decision | Status |
|----------|--------|
| Loop shape = Integrated Operator + Employee Mobile V2 | **AFFIRMED** |
| Thin backend capability/read projections allowed | **AFFIRMED** |
| Mobile surface = `/employee-app-v2` only; V1 unchanged | **AFFIRMED** |
| Phase 2 architecture closed (nonblocking limitations OK) | **ACCEPTED** |
| Implementation not authorized until GO | **BINDING** |

---

## Plan-locked design (accepted by signing G1)

| Lock | Value |
|------|-------|
| Primary Operator surface | `/execution/:orderId` RealityCapturePanel task collaboration chrome |
| Secondary Operator surface | `/operator` current-task thin mirror |
| Helper discovery | Mobile V2 Tasks **Ajutor** section (`help-opportunities`) |
| Helper work | Mobile V2 task detail / work room |
| Shared FE | Typed API client + types; surface-specific render adapters |
| Optimistic help UI | **No** — refetch after commands |
| Feature flag | `VITE_FEATURE_FLEX_COLLAB_UI` default off |
| Backend kill switch | `FLEX_COLLAB_PHASE2_ENABLED` |
| Thin caps | `can_request_help`, `can_cancel_help`, viewer-scoped collab-read `can_*` |
| Migration | **None** |
| Playwright collab E2E | Deferred |

---

## Phase-level decisions required (owner GO)

| ID | Question | Plan recommendation | Owner answer |
|----|----------|---------------------|--------------|
| **G1** | Authorize Phase 3 integrated Operator + Mobile V2 one-GO? | **YES** | _pending_ |
| **G2** | Authorize thin capability projections only (no Phase 2 redesign, no migration)? | **YES** | _pending_ |
| **G3** | Primary request surface = ExecutionDetail; OperatorView = thin mirror? | **YES** | _pending_ |
| **G4** | Employee Mobile V2 only; V1 untouched? | **YES** | _pending_ |
| **G5** | Ship UI behind `VITE_FEATURE_FLEX_COLLAB_UI` default off until proof? | **YES** | _pending_ |
| **G6** | Defer Playwright, leave+stop combo, timeline, quotas, workcenter pool? | **YES** | _pending_ |

---

## Explicit non-goals (confirm by GO)

- No mock collaboration data  
- No Product System / snapshots / pricing  
- No broad navigation or theme redesign  
- No TabletMode demo “Ajutor” as product path  
- No frontend inference of eligibility/authority/membership/help status  

---

## Options rejected (documented)

| Option | Why rejected for Phase 3 GO |
|--------|------------------------------|
| Mobile-first only | Incomplete loop without product request surface |
| Operator-first only | No floor helper work |
| Shared mega-panel first | Abstraction without end-to-end journey |

---

## After GO

Run `/ce-work` on `.compound-engineering/prod-flex-collaboration-phase-3/plan.md` only. Do not start Phase 3 implementation from this decision log alone without G1–G6.
