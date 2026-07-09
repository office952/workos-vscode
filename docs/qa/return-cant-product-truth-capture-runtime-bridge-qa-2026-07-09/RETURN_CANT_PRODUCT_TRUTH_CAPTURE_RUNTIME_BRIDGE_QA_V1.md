# RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_QA_V1

Decision: RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_QA_PASS

## Scope

- Read-only QA for committed runtime bridge `return_cant`
- No code changes expected
- No UI, Pricing, runtime DB pricing, Quote/Order/Execution, ProductAggregate, TaskGraph, ExecutionPlan, migration, or manual seed work

## HEAD

- HEAD before QA: `7ec9d9b`
- HEAD after QA docs commit: `pending at document authoring time`

## Safety Gate

- `git status -sb`: no staged files; unrelated pre-existing untracked files remain in worktree
- `git rev-parse --short HEAD`: `7ec9d9b`
- `git diff --cached --name-only`: empty
- `git diff --check`: clean

## Tests Run

Command:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_return_cant_product_truth_bridge.py tests/test_letter_group_finish_readiness.py -q
```

Result:

- `22 passed`

Observed coverage relevant to this QA:

- pure helper derivation for letter groups and artwork layers
- idempotence and no legacy writeback checks
- stable-key skip behavior
- pricing key normalization checks for stock/vinyl/paint
- workspace endpoint integration for save/clear lifecycle through TestClient

## Helper QA

Verdict: pass

Confirmed from `backend/services/return_cant_product_truth_bridge.py`:

- helper is pure and testable
- no DB access
- no filesystem or network IO
- no live Pricing lookup
- writes only under `product_truth.components.return_cant`
- does not write legacy `components.returnCant`
- `apply_return_cant_runtime_product_truth_bridge()` is idempotent for the same payload
- missing `group_key` / `layer_key` rows are skipped; no synthetic `instance_key` is invented

Canonical output confirmed:

- `product_truth.components.return_cant.version = "v1"`
- `instances["letter_group:<group_key>"]` for letter groups
- `instances["artwork_layer:<layer_key>"]` for artwork layers

## Schema QA

Verdict: pass

Confirmed from `backend/schemas/intake_v4.py`:

- `IntakeV4WorkspacePayload` explicitly preserves `product_truth: dict[str, Any] | None = None`
- existing payloads without `product_truth` remain compatible because the field is optional and defaults to `None`

## Wiring QA

Verdict: pass

Confirmed from `backend/services/intake_v4_workspace_service.py` and `backend/services/intake_v6_workspace_service.py`:

- bridge applies on finish setup save
- bridge reruns on relevant upstream mutations when finish setup remains present:
  - analysis bundle save
  - layer role updates
  - SVG upload when file is not considered a replacement and finish setup still exists
- bridge is cleared when SVG replacement invalidates finish setup
- stale `return_cant` subtree is removed after invalidation

## Runtime/API Smoke

Verdict: pass via committed endpoint integration tests

Notes:

- live-server mutation smoke was not executed against the local backend process because this QA slice is read-only and should not create/update real workspace data outside the test boundary
- API-path smoke is covered by committed workspace-level integration tests in `backend/tests/test_return_cant_product_truth_bridge.py`
- those tests exercise:
  - workspace create endpoint
  - analysis bundle save
  - finish setup save with `letter_group_finishes`
  - finish setup save with `artwork_finishes`
  - payload readback assertions
  - stale clear after SVG replacement

Confirmed output shape from those integration tests:

- `product_truth.components.return_cant.version == "v1"`
- `product_truth.components.return_cant.instances` exists after finish setup save
- letter group instance key uses `letter_group:<group_key>`
- artwork layer instance key uses `artwork_layer:<layer_key>`
- source refs preserve `group_key` and `layer_key`

## Product Truth Output Example

```json
{
  "product_truth": {
    "components": {
      "return_cant": {
        "version": "v1",
        "instances": {
          "letter_group:pseudo:maria": {
            "instance_key": "letter_group:pseudo:maria",
            "source_kind": "letter_group",
            "source_ref": {
              "group_key": "pseudo:maria",
              "source_label": "maria",
              "source_role": "Vector Litere"
            },
            "layer_group_ids": ["pseudo:maria"],
            "material_profile": {"width_mm": 60},
            "finish_variant": {
              "type": "stock_color",
              "stock_color_label": "Alb"
            },
            "pricing_keys": {
              "material_profile_width": "MAT-PROFIL-LATERAL-LITERE-60MM"
            },
            "geometry": {
              "perimeter_source": "evidence_only",
              "evidence_perimeter_m": 18.5
            },
            "confirmation_state": "blocked",
            "blockers": [
              "RETURN_CANT_CONFIRMED_PERIMETER_MISSING",
              "RETURN_CANT_PERIMETER_EVIDENCE_ONLY",
              "RETURN_CANT_COMPONENT_CONFIRMATION_MISSING"
            ]
          }
        }
      }
    }
  }
}
```

## State And Blockers Verification

Verdict: pass

Confirmed against helper logic, tests, and contracts:

- `quote_geometry.letter_perimeter_m` remains evidence only
- `geometry.confirmed_perimeter_m` is not authored from quote geometry
- `confirmation_state` does not become `confirmed` from row confirmation, finish setup confirmation, or geometry presence
- missing `layer_group_ids` yields blocker state
- missing width / finish mapping / required color token yields `RETURN_CANT_PRICING_KEYS_MISSING`
- missing stable key yields no instance, not a synthetic key

Pricing key verification:

- vinyl application emits:
  - `RETURN_CANT_VINYL_APPLICATION_LABOR`
  - `MAT-ORACAL-641` or `MAT-ORACAL-651`
- paint application emits:
  - `RETURN_CANT_RAL_PAINT_LABOR`
  - width-specific `MAT-VOPSEA-RAL-CANT-30MM|60MM|80MM|100MM`
- stock color emits no vinyl/paint labor or material key and preserves profile material when width is valid

## Forbidden Scope Confirmation

- no UI changes
- no Pricing changes
- no runtime DB pricing writes
- no seed run outside test execution
- no Quote/Order/Execution changes
- no ProductAggregate/TaskGraph/ExecutionPlan changes
- no DB migration
- no code changes expected for QA; only docs are authored in this slice

## Honest Verdict

The committed bridge is aligned with the documented runtime container, confirmation, perimeter-source, and layer-mapping contracts for the minimal backend writer slice. The main deliberate limitations remain the same as in implementation:

- no global diagnostics object for skipped rows
- no confirmed perimeter writer
- no component-confirmed state promotion path yet

These are roadmap limitations, not QA blockers for this committed minimal bridge.

## Next Recommended Prompt

`RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_FRONTEND_AWARENESS_RECHECK_V1`