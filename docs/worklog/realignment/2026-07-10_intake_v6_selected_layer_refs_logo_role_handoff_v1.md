# Intake V6 — Selected Layer Refs & Logo Role Handoff (V1)

**Date:** 2026-07-10
**Task:** INTAKE_V6_SELECTED_LAYER_REFS_AND_LOGO_ROLE_HANDOFF_V1
**Verdict:** **PASS**
**Accepted HEAD:** `6ab94b8`
**Branch:** `main`
**Commit:** _pending_

---

## Owner decisions applied

- **DEC-FHA-01A:** `layer_role_setup` canonical; `selected_layer_refs` derived projection only.
- **DEC-FHA-02A:** `face` → `vector_litere`; `printed_artwork` → `vector_logo`.
- **DEC-FHA-03:** NOT INCLUDED (linked template binding).
- **Historical backfill:** NOT INCLUDED.

---

## Architecture readback

| Path/function | Reads | Writes | Canonical/Derived | Risk (before) |
| --- | --- | --- | --- | --- |
| `layer_role_setup` PUT (analysis-bundle, layer-roles) | operator | **canonical** | — | OK |
| `_SELECTED_LAYER_ROLE_MAP` | confirmed_role | — | mapping | Missing `printed_artwork` |
| `derive_selected_layer_refs_from_setup` | layer_role_setup | — | derived | **NEW shared pure helper** |
| `selected_layer_refs_runtime_state` | layer_role_setup | — | derived | Used auto_role filter; logo gap |
| `sync_selected_layer_refs_on_payload` | setup | svg.selected_layer_refs | derived persist | Cleared key when empty |
| `_sync_selected_layer_refs` (v4/v6) | payload | via sync helper | derived persist | Duplicate logic |
| `product_truth_promotion_planner._classify_selected_layer_entries` | persisted + setup | — | read | Blocked when not persisted |
| `form_system_contract_backbone` overlay | both | — | verify | Compares persisted vs runtime |

**Sync runs after:** analysis-bundle save, layer-roles save (v4 + v6 workspace services).

---

## Current flow before fix

1. Operator confirms roles in `layer_role_setup`.
2. `_sync_selected_layer_refs` called on canonical write path.
3. Map only had `face` + legacy `logo`; `printed_artwork` skipped.
4. Sync only persisted when `runtime["refs"]` non-empty; otherwise popped key → historical drift (fixture has complete setup, no persisted refs).
5. Promotion planner required persisted refs; logo layers invisible in derived projection.

---

## Canonical source and derived projection

- **Canonical:** `payload_json.layer_role_setup`
- **Derived:** `payload_json.svg.selected_layer_refs`
- **Conflict rule:** canonical wins; sync recomputes projection without rewriting operator roles.

---

## Role map before / after

**Before:**
```python
{"face": "vector_litere", "logo": "vector_logo"}
```

**After:**
```python
{
    "face": "vector_litere",
    "printed_artwork": "vector_logo",
    "logo": "vector_logo",  # LEGACY_BRIDGE
}
```

---

## Implementation

1. Added `derive_selected_layer_refs_from_setup()` — pure, deterministic, confirmed layers only, workspace layer order, per-layer skip for unknown/ignored/unconfirmed.
2. Refactored `selected_layer_refs_runtime_state()` to use shared helper; empty complete setup → `status=confirmed`, `blocker_code=SELECTED_LAYER_REFS_EMPTY`.
3. Added `sync_selected_layer_refs_on_payload()` — single shared persist path; persists `[]` when confirmed-empty; pops key when unconfirmed/ambiguous.
4. v4 + v6 workspace services delegate to shared sync helper.
5. Promotion planner read path: when persisted refs absent but canonical setup derives refs → blocked entries with `value_status=derived_at_read_time`, `SELECTED_LAYER_REFS_NOT_PERSISTED` (no false READY).

---

## Empty-result semantics

| Situation | Persisted projection | Notes |
| --- | --- | --- |
| Setup incomplete | key removed | Not authoritative empty |
| Ambiguous identity | key removed | Duplicate/missing layer_id |
| Complete, zero mappable confirmed layers | `[]` | Intentional empty |
| Complete, mappable layers | ref list | Normal path |

Unrelated SVG metadata preserved; entire `svg` object not removed when only refs cleared.

---

## Linked logo boundary

- `printed_artwork` → `vector_logo` in derived refs only.
- No linked template binding invented.
- No logo finish auto-confirmation.
- Promotion/read still blocked for missing binding/finish (existing blockers remain).

---

## Tests

```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
.\.venv\Scripts\python.exe -m pytest `
  tests/test_selected_layer_refs_derivation.py `
  tests/test_selected_layer_refs_runtime_capture.py `
  tests/test_product_truth_promotion_planner_service.py `
  tests/test_form_system_contract_backbone.py `
  tests/test_product_definition_builder.py `
  tests/test_product_definition_gradi_composition.py `
  tests/test_return_cant_product_truth_bridge.py -q
```

**Result:** 82/82 PASS (task-scoped batch).

New coverage: mapping (face, printed_artwork, legacy logo, unknown, ignored, unconfirmed), mixed 4+2 composition, sync idempotency, empty array, promotion read-time block + persisted vector_logo.

**Note:** `test_product_aggregate_volumetric_v2.py` has 3 pre-existing failures unrelated to this slice (parent components seed state); not modified.

---

## Runtime read-only verification

Local SQLite dev DB unavailable in agent environment → live HTTP GET not run against running stack.

**Read-only capture verification** (fixture `22ef834d-f2d0-453b-a7a7-118928c98a39`, audit capture `docs/qa/intake-v6-functional-handoff-audit-v1/captures/workspace.json`):

| Check | Expected | Actual |
| --- | --- | --- |
| Persisted `selected_layer_refs` | absent (no backfill) | `None` |
| Recomputed projection | 4× `vector_litere`, 2× `vector_logo` | confirmed |
| Runtime status | `confirmed` | `confirmed` |
| Fixture mutated | NO | NO |

Historical impact audit script: `docs/qa/intake-v6-selected-layer-refs-logo-role-handoff-v1/historical_impact_audit.py` → **NOT_RUN** (no local sqlite file).

---

## Files changed

- `backend/services/intake_v4_layer_role_service.py`
- `backend/services/intake_v4_workspace_service.py`
- `backend/services/intake_v6_layer_role_service.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/product_truth_promotion_planner_service.py`
- `backend/tests/test_selected_layer_refs_derivation.py` (new)
- `backend/tests/test_selected_layer_refs_runtime_capture.py`
- `backend/tests/test_product_truth_promotion_planner_service.py`
- `docs/worklog/realignment/2026-07-10_intake_v6_selected_layer_refs_logo_role_handoff_v1.md`
- `docs/qa/intake-v6-selected-layer-refs-logo-role-handoff-v1/historical_impact_audit.py`

---

## Forbidden scope confirmed

No UI, frontend application, DB schema, migration, seed, historical backfill, pricing, ProductSystem/ProductDefinition architecture changes, Quote/Order/Execution, SVG parsing, negative-hole, E2E, Employee Mobile.

---

## Honest opinion

This is the correct minimal repair: one pure derivation helper, one sync path, logo mapping added without elevating `selected_layer_refs` to truth. Historical workspaces remain drifted until re-save or an explicit backfill GO. Read-time derivation in the promotion planner makes the gap visible without inventing persistence.

---

## Remaining gaps

- FHA-03 linked template binding persistence (owner pending).
- FHA-05 ProductDefinition duplicate rows (out of scope).
- FHA-06 aggregate template-only warnings (out of scope).
- Historical workspaces without re-save still lack persisted projection.

---

## Owner decisions still pending

- DEC-FHA-03: linked logo template binding persistence strategy.
- Historical backfill GO (if impact audit shows material drift).

---

## Next safe step

Re-save or run a controlled backfill pilot on workspaces with complete `layer_role_setup` and missing `selected_layer_refs` **after** owner reviews read-only impact audit on production/staging DB.

---

## Direction score

**92/100** — aligns with post-audit functional repair roadmap; defers binding/backfill correctly.

**Roadmap awareness:** 9/10

---

## Delivery footer

| Item | Value |
| --- | --- |
| printed_artwork → vector_logo | YES |
| face → vector_litere | YES |
| Mixed letters + logo verified | YES (tests + capture) |
| Persistence verified | YES (v4 write-path tests) |
| Historical backfill | NO |
| Fixture mutated | NO |
| Backend changed | YES |
| Frontend changed | NO |
| DB schema changed | NO |
| Worklog | YES |
| Ready for next owner decision | YES |
