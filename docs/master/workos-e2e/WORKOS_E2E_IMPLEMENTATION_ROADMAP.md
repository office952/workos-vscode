# WorkOS E2E — Implementation Roadmap

**Program:** `WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1`  
**HEAD:** `fe6c6f7`  
**Operating model:** `WORKOS_E2E_IMPLEMENTATION_OPERATING_MODEL.md`  
**Hold:** YES until owner approves operating model + P-001 for Wave 1

## Wave overview

| Wave | Name | Code changes | Owner gate |
|------|------|--------------|------------|
| 0 | Baseline & governance | NO | This program — **complete** |
| 1 | Intake canonical truth | YES | **First after approval** |
| 2 | PD & Aggregate | YES | After Wave 1 handoff safe |
| 3 | Cost authority | YES | After Wave 2 graph stable |
| 4 | Offer & Order | YES | After Wave 3 pricing traceable |
| 5 | Execution | YES | After Wave 4 freeze proven |
| 6 | Operator UI | YES | After Waves 1–5 logic stable |
| 7 | Final E2E acceptance | TEST + seed (owner GO) | After Wave 6 |

---

## Wave 0 — Baseline and governance ✅

- Master dossier + 8 companion docs
- Issue registry consolidation
- Document index + supersession
- Figma MASTER spec (0/14 physical pages)
- Agent operating contract

**No application code.**

---

## Wave 1 — Intake canonical truth

**Goal:** One mounting/readiness/handoff truth channel.  
**Orchestration:** Serialized lanes — see operating model §9. **No implementation parallelism on spine.**

| Lane ID | Title | Issues | Depends |
|---------|-------|--------|---------|
| W1-L-SPINE | `INTAKE_V6_CANONICAL_READINESS_TRUTH_SPINE_V1` | TE2E-001,002,014,015 | F-001 closed |
| W1-INT-01 | Spine integration proof | — | W1-L-SPINE |
| W1-L-FINISH | `INTAKE_V6_FINISH_TRUTH_PERSISTENCE_V1` | TE2E-003 | W1-INT-01 |
| W1-L-CANT | Cant/return finish contract | TE2E-006 | W1-L-FINISH |
| W1-INT-02 | **Wave 1 integration gate — opens Wave 2** | — | W1-L-CANT |
| W1-L-VECTOR | Vector analyzer edge (optional) | TE2E-007 | W1-INT-02 |

**Forbidden:** PD UI, CostEngine refactor, badge-only hiding, parallel spine implementation.

---

## Wave 2 — Product Definition & Aggregate

| Task ID | Title | Issues | Depends |
|---------|-------|--------|---------|
| W2-T01 | Resume PD composition contract (Cases A–D) | TE2E-010 partial | W1 complete |
| W2-T02 | Aggregate handoff without re-inference | TE2E-026 | W2-T01 |
| W2-T03 | PD operator surface (embedded or route) | TE2E-010,011 | W2-T01 |

---

## Wave 3 — Cost authority (D-010 decided)

| Task ID | Title | Issues | Depends |
|---------|-------|--------|---------|
| W3-D010 | Cost authority decision | TE2E-025 | W2-INT-01 | **COMPLETE** |
| W3-T01 | Graph-to-cost module projection adapter | TE2E-025 | W3-D010 |
| W3-T02 | V6 commercial spine alignment (7G official) | TE2E-025 | W3-T01 |
| W3-T03 | Snapshot unify + pricing registry completeness | TE2E-008, TE2E-025 | W3-T02 |

---

## Wave 4 — Offer & Order

| Task ID | Title | Issues | Depends |
|---------|-------|--------|---------|
| W4-T01 | Offer readiness = merged blockers + graph | TE2E-014 downstream | W3-T02 |
| W4-T02 | Order freeze immutability proof | TE2E-022 | W4-T01 |

---

## Wave 5 — Execution

| Task ID | Title | Issues | Depends |
|---------|-------|--------|---------|
| W5-T01 | Execution plan from frozen snapshot | — | W4-T02 |
| W5-T02 | Task generation + dependency preservation | — | W5-T01 |
| W5-T03 | Auth stability for execution routes | TE2E-023 | parallel |

---

## Wave 6 — Operator UI

| Task ID | Title | Issues | Depends |
|---------|-------|--------|---------|
| W6-T01 | Intake Step 2 surface simplification | TE2E-005 | W1 complete |
| W6-T02 | Terminology pass | TE2E-009,026 | W1–3 |
| W6-T03 | PD Figma alignment | TE2E-011 | W2-T03 |
| W6-T04 | PS stub tab gating | TE2E-012 | — |
| W6-T05 | Offers/Orders debug relocation | TE2E-020,021 | W4 |
| W6-T07 | Execution typography | TE2E-024 | W5 |

---

## Wave 7 — Final E2E acceptance

| Task ID | Title | Issues | Depends | Status |
|---------|-------|--------|---------|--------|
| W7-T01 | Controlled same-scenario seed + full spine test | TE2E-013 | Owner GO + Waves 1–6 | **COMPLETE — PROVEN_V1** (2026-07-17; `DETERMINISTIC_LOCAL_SCENARIO`; commits `4da68ed`→`ad25fa9`→`91d8a3f`) |
| W7-T02 | Reconciliation proof | — | W7-T01 | **NEXT / not started** |
| W7-T03 | Owner sign-off checklist | All P1 + accepted P2 | W7-T02 | open |

**Build 1 closure:** same-scenario Request→Post-Job proven on IR `IR-BUILD1-1784237119` / order `92402`. Residual limitations tracked as TE2E-028. Do not treat as universal template proof.

---

## Parallel-safe (orchestration-corrected)

- W1-L-VECTOR — only after W1-INT-02 if file-independent
- W5-T03 ∥ W5-T01 — coordinator reserves auth file overlap
- W6-T04 — after W1 logic; coordinator approval required
- ~~W1-T04 ∥ W1-T02~~ — **revoked**

## Blocked until upstream

- All Wave 2+ until Wave 1 merges
- W7 until owner GO on seed
- PD frontend until handoff safe

## Irreversible decisions (require owner)

- Cost authority single owner (W3-T01)
- PD standalone route vs embedded (W2-T03)
- E2E seed fixture policy (W7-T01)
