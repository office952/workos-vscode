# WorkOS E2E — Acceptance Plan

**Program:** `WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1`  
**Operating model:** `WORKOS_E2E_IMPLEMENTATION_OPERATING_MODEL.md`  
**Final scenario:** Controlled volumetric letters path (owner GO required for seed)  
**Living progress:** Gate closure recorded in `WORKOS_E2E_STATUS.md` / DECISION_LOG — this plan defines the gates, not which are currently green.  
**B2:** Outside Important Documents unless owner promotes.

## Orchestration gates (in addition to definition of done)

| Gate level | When | Authority |
|------------|------|-----------|
| Task gate | Each lane closure | Lane worker + coordinator review |
| Wave integration gate | End of each wave | Wave Coordinator (§5 operating model) |
| Cross-wave opening gate | Before next wave code | Coordinator + owner where required |

Local task PASS **never** automatically opens the next wave.

## Definition of done (20 gates)

| # | Gate | Verification |
|---|------|--------------|
| 1 | One product truth survives all stages | Same root template + child IDs end-to-end |
| 2 | Ownership unambiguous | SYSTEM_MAP + decision log |
| 3 | State transitions valid | No ready+blockers |
| 4 | Readiness matches blockers | capture ⊆ readiness |
| 5 | No downstream re-inference | Order snapshot = Offer graph |
| 6 | Cost authority singular | One traceable calculation graph |
| 7 | Offer and Order same graph | Snapshot diff = empty |
| 8 | Order snapshot immutable | PATCH rejected post-freeze |
| 9 | Execution consumes frozen truth | tasks from snapshot only |
| 10 | Actuals reconcile to plan | reconciliation record |
| 11 | One clear primary action per operator page | UX audit pass |
| 12 | Warnings actionable | each maps to correction route |
| 13 | Diagnostics off operator path | MASTER 07/08 parity |
| 14 | Terminology aligned | terminology matrix green |
| 15 | Figma matches runtime | MASTER frames ↔ screenshots |
| 16 | All P1 issues closed | ISSUE_REGISTRY |
| 17 | Required P2 closed or accepted | owner sign-off list |
| 18 | Final same-scenario E2E passes | W7-T01 |
| 19 | Documentation consolidated | DOCUMENT_INDEX canonical only |
| 20 | Owner signs off | written approval in DECISION_LOG |

---

## Same-scenario acceptance (Wave 7)

**Baseline fixture (existing):**

| Field | Value |
|-------|-------|
| Request | `IR-MRJS4VIK` |
| Workspace | `80570a4a-a806-4305-a39c-b34a72092694` |
| SVG | `gradi-curat.svg` |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Montaj | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |

**Required proof chain (after Waves 1–6):**

| Artifact | ID field | Gate |
|----------|----------|------|
| Request | `IR-MRJS4VIK` | preserved |
| Workspace | UUID | preserved |
| Product identity | root + child template codes | preserved |
| Component identities | component_id set | preserved |
| Composition edges | module triggers | preserved |
| Dimensions/materials/finishes | aggregate fields | preserved |
| Mounting | mounting_solution | preserved |
| Cost | priced lines hash | preserved Offer→Order |
| Commercial price | quote totals | frozen at accept |
| Offer ID | quote UUID | created |
| Order ID | order UUID | from accept |
| Snapshot | snapshot v2 hash | immutable |
| Execution plan ID | plan reference | from order |
| Tasks | task IDs + deps | from frozen ops |
| Actuals | captured times | reconcile |
| Final status | reconciliation | closed |

**Seed policy:** No DB mutation without explicit owner GO. Plan defines script path: `backend/scripts/seed_commercial_e2e_fixture.py` (existing) — owner approves when Wave 7 starts.

---

## Per-wave acceptance gates

### Wave 1
- pytest: capture + readiness + handoff policy merge wired
- Runtime: IR-MRJS4VIK step 2 — zero false ready, zero SUPPORT_TYPE with ACM saved
- W1-INT-02 integration gate before Wave 2 entry
- Screenshots: before/after step 2–3

### Wave 2
- API: PD preview + aggregate GET consistent with Intake
- Composition Cases A–D deterministic tests

### Wave 3
- Single cost trace document in DECISION_LOG
- 21/21 pricing rows or explicit blockers

### Wave 4
- Quote create from handoff dry-run
- Order snapshot byte-stable on reload

### Wave 5
- Execution dashboard row for seeded order
- Tasks match frozen operations

### Wave 6
- Operator UI audit: no capture accordion on step 2
- Offers page: no policy debug banner

### Wave 7
- Playwright or scripted spine: intake → quote → order → execution
- Full screenshot index for reviewer package

---

## Test commands (reference)

```powershell
# Wave 1 targeted
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_system_identity_boundary.py -q

# Frontend scoped
npm run test:frontend -- src/components/workos/intake-v6/steps/IntakeV6ReviewStep.commercialSettings.test.tsx
```

Full suite not gate until debt addressed per AGENTS.md.
