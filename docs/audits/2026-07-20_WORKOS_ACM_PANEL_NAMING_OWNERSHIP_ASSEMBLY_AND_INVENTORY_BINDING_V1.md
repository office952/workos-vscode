# WORKOS_ACM_PANEL_NAMING_OWNERSHIP_ASSEMBLY_AND_INVENTORY_BINDING_V1

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Mode | Implementation Slice A+B — **STOP for owner review** |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Fixture | `IV6-DB2F86B7` / `a7b0162b-dc91-467f-aa24-c1279fb3a073` |
| Evidence | [`docs/audits/_evidence/2026-07-20_acm-panel-naming-assembly-binding/`](./_evidence/2026-07-20_acm-panel-naming-assembly-binding/) |
| Plan | [`docs/plans/2026-07-20_WORKOS_ACM_PANEL_NAMING_OWNERSHIP_ASSEMBLY_AND_INVENTORY_BINDING_V1.md`](../plans/2026-07-20_WORKOS_ACM_PANEL_NAMING_OWNERSHIP_ASSEMBLY_AND_INVENTORY_BINDING_V1.md) |
| Worklog | [`docs/worklog/realignment/2026-07-20_acm_panel_naming_ownership_assembly_and_inventory_binding_v1.md`](../worklog/realignment/2026-07-20_acm_panel_naming_ownership_assembly_and_inventory_binding_v1.md) |

## Verdict

**PASS (implementation complete for Slice A+B)** — assembly keys explicit; ACM-root PD parity with provenance; preferred SKU naming; fixture invariants held; commercial formulas untouched.

## What shipped

1. **Shared assembly extent** (FE + BE, 1 mm tolerance) → `assembly_width_mm` / `assembly_height_mm`.
2. **Blueprint L1-P** consumes shared helper — no regression (UI proof 2000×350).
3. **Letters PD** injects assembly keys from coalesced AcmPanel + segmented proposal.
4. **ACM-root PD** cross-template read when workspace has real AcmPanel:
   - provenance `linked_workspace_template_code`
   - provenance `read_mode=cross_template_acm_parity`
   - no new instance / lifecycle / owner
5. **Quote merge** injects assembly keys without switching CostEngine/CPP area off `panel_*`.
6. **Naming:** `MAT-ACM-BOND-3MM` preferred; `MAT-ACP-3MM` legacy alias notes (no delete/migration).
7. **PROFILE-SHS-20X20X1_5** untouched (remains fixing-only).

## Runtime proof (`pd-assembly-proof.json`)

| Root | `assembly_*` | Envelope ignored | Notes |
|------|--------------|------------------|-------|
| Letters | 2000×350 | true | tech proposed, composition unconfirmed, seg PROPOSED |
| ACM boxed | 2000×350 | true | `panel_width_mm=1000` still present (commercial Slice C) |

## Tests

| Suite | Result |
|-------|--------|
| `test_acm_assembly_extent.py` + PD proposal + cross-template | **8 passed** |
| Vitest `assemblyExtent` + `blueprintReadModel` | **22 passed** |
| UI capture | **PASS** 2000×350 |

## Slice C blockers (must not silently price)

1. Active commercial derivation still uses `panel_width_mm` / `panel_height_mm`.
2. Multi-panel ACM-root can expose envelope 1000 alongside assembly 2000 — pricing must prefer `assembly_*`.
3. No Pricing Preview / Offer / Execution activation in this build.

## Boundaries respected

- No seed `task_rules` edits
- No MIXED DAG copy
- No Offer/Order/Execution writes
- No CostEngine formula change
- Blueprint authority model unchanged (L1-P provisional)

## Owner gates

1. Accept assembly key names + PD parity provenance.
2. Accept deferral of commercial area switch to Slice C.
3. Accept `MAT-ACM-BOND-3MM` preferred / `MAT-ACP-3MM` legacy without migration.
4. Confirm fixture posture unchanged for final price / Execution blocked.
