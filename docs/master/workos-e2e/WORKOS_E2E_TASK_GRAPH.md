# WorkOS E2E — Task Graph

**Program:** `WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1`  
**Operating model:** `WORKOS_E2E_IMPLEMENTATION_OPERATING_MODEL.md`  
**Active task:** None (hold — orchestration model pending owner approval)  
**First task after P-001:** `W1-L-SPINE` — `INTAKE_V6_CANONICAL_READINESS_TRUTH_SPINE_V1`

## Orchestration rule

Task IDs below are **lanes** under wave coordinator control. Parallel assumptions in legacy graph are **superseded** by the operating model collision analysis.

## Task template (all implementation tasks must include)

- task ID, root cause, owner system, upstream dependency, downstream consumers
- files likely affected, forbidden scope, test commands, runtime routes
- screenshot requirements, Figma references, success criteria, rollback
- worklog path, commit requirement, next task

**DONE criteria:** tests pass, runtime proof, screenshots (UI), issue registry updated, status updated, isolated commit.

---

## Wave 1 — Intake canonical truth (orchestrated)

**Integration owner:** Wave Coordinator  
**Implementation parallelism:** FORBIDDEN on spine (see operating model §9)

### W1-L-SPINE — INTAKE_V6_CANONICAL_READINESS_TRUTH_SPINE_V1

| Field | Value |
|-------|-------|
| Status | **COMPLETE** (W1-INT-01 LIVE PASS — 2026-07-14) |
| Replaces | Legacy W1-T01 (scope expanded) |
| Root cause cluster | TE2E-001, 002, 014, 015 — shared readiness spine |
| Owner | Intake / FormSystem |
| Collision risk | CRITICAL — serialize only |
| Delivers | mounting_solution gate (D-005); readiness merges capture (D-006); wire merge_policy_findings; no false ready |
| Files likely | `form_system_runtime_capture_read_model_service.py`, `form_system_contract_backbone_service.py`, `intake_v6_workspace_service.py`, `intake_v6_canonical_readiness_service.py`, handoff callers, frontend readiness/blocker |
| Forbidden | PD, CostEngine, UI-only badge hide, new audit |
| Integration | W1-INT-01 after merge |
| Next | W1-L-FINISH |

### W1-L-FINISH — INTAKE_V6_FINISH_TRUTH_PERSISTENCE_V1

| Field | Value |
|-------|-------|
| Status | **COMPLETE** (2026-07-14) |
| Upstream | W1-INT-01 PASS |
| Issues | TE2E-003 |
| Collision | HIGH — shares finish_setup |
| Delivers | hydrate `finish_target` + artwork booleans at save; capture/readiness/handoff alignment |
| Next | W1-L-CANT |

### W1-L-CANT — Cant/return finish contract

| Field | Value |
|-------|-------|
| Status | **COMPLETE** (2026-07-14) |
| Upstream | W1-L-FINISH |
| Issues | TE2E-006 |
| Delivers | `product_truth.return_cant` → review canonicalRuntime; save normalization; runtime capture overlay |
| Next | W1-INT-02 |

### W1-INT-02 — Wave 1 integration gate

| Field | Value |
|-------|-------|
| Status | **COMPLETE — PASS** (2026-07-14) |
| Verdict | `W1_INT_02_PASS_WITH_NONBLOCKING_DEBT_OPEN_WAVE_2` |
| Proof | IR-MRJS4VIK step 2–3; API trace; 3 UI screenshots |
| Issues verified | TE2E-001, 002, 003, 006, 014, 015 |
| Opens | **Wave 2** |
| Next | W2-T01 |

### W1-L-VECTOR — Residual vector analyzer edge (optional)

| Field | Value |
|-------|-------|
| Issues | TE2E-007 |
| Parallel | Only after W1-INT-02 if file-independent |
| Note | Legacy W1-T04 parallel claim **revoked** |

---

## Legacy reference — W1-T01 (superseded by W1-L-SPINE)

| Field | Value |
|-------|-------|
| Root cause | Legacy `support_type` gate + readiness derive ignore `mounting_solution` and capture blockers |
| Owner | Intake / FormSystem |
| Upstream | F-001 closed (`fe6c6f7`) |
| Downstream | PD handoff, Offer policy, operator UX (TE2E-005 exposed) |
| Issues | TE2E-001, 002, 014, 015 |
| Files likely | `form_system_runtime_capture_read_model_service.py`, `intake_v6_workspace_service.py`, `intakeV6OperatorBlockerBannerDisplay.ts`, handoff policy services |
| Forbidden | PD implementation, CostEngine refactor, UI-only badge hiding |
| Tests | Targeted pytest capture/readiness; Vitest blocker banner |
| Runtime routes | `/intake-v6/IR-MRJS4VIK/operator` step 2 |
| Fixture | workspace `80570a4a-a806-4305-a39c-b34a72092694` |
| Screenshots | Step 2 before/after — single blocker channel |
| Figma | MASTER 04, PD03 |
| Success | No SUPPORT_TYPE_MISSING with ACM saved; no ready badge with blockers; handoff merges capture |
| Worklog | `docs/worklog/realignment/2026-07-XX_intake_v6_canonical_mounting_blocker_alignment_v1.md` |
| Next | W1-L-FINISH |

---

## Waves 2–7 (unchanged IDs — see operating model §10)

## W2-T01 — PD composition resume

| Issues | TE2E-010 (partial) |
| Upstream | W1-INT-02 PASS (Wave 1 integration gate) |
| Files | `product_definition_composition_contract.py`, builder service |
| Forbidden | Offer/Order changes |
| Next | W2-T02 |

---

## W3-T01 — Cost authority alignment

| Issues | TE2E-025 |
| Upstream | W2-T02 |
| Decision required | Single traceable graph owner (D-010) |
| Next | W3-T02

---

## W7-T01 — Final same-scenario E2E

| Issues | TE2E-013, 022 |
| Upstream | Waves 1–6 + **owner GO on seed** |
| Proof | Full ID chain in ACCEPTANCE_PLAN |
| Forbidden without GO | DB seed, migration |

---

## Dependency graph (ASCII)

```
F-001 (closed)
    ↓
W1-L-SPINE → W1-INT-01 → W1-L-FINISH → W1-L-CANT → W1-INT-02
    ↓
W2-T01 → W2-T02 → W2-T03
    ↓
W3-T01 (owner D-010) → W3-T02
    ↓
W4-T01 → W4-T02
    ↓
W5-T01 → W5-T02
    ↓
W6-* (after W1 logic; coordinator reserves collisions)
    ↓
W7-T01 → W7-T03 (owner sign-off)
```

## Parallel lanes (orchestration-corrected)

- W1-L-VECTOR — only after W1-INT-02 if independent (not ∥ W1-L-FINISH)
- W5-T03 ∥ W5-T01 — only if auth files reserved separately
- W6-T04 — after W1 logic; coordinator checks file overlap
- ~~W1-T04 ∥ W1-T02~~ — **revoked** (finish_setup collision)
