# 2026-07-16 — Runtime capture blocker contract alignment

## Previous two shapes

Field-level (allowed root):

```json
{ "field_key": "...", "blockers": ["..."], "state": "..." }
```

Logo / fail-closed backbone (raw dump when `root.allowed=false`):

```json
{ "blocker_code": "LOGO_NOT_OFFERABLE", "severity": "blocked", "message": "...", "blocks": [] }
```

`blocks` = downstream surfaces; `blockers` = code list. Not interchangeable.

## Consumers

| Consumer | Expectation |
|----------|-------------|
| `intakeV6OperatorBlockerBannerDisplay` | `row.blockers[]` (+ defensive `asBlockerCodeList`) |
| `intakeV6ReviewDiagnosticEntryCount` | same |
| Runtime-capture HTTP/unit tests | field shape + fail-closed semantics |
| Readiness / quote-handoff | separate endpoints; must stay unchanged |

## Options considered

- **A — Additive normalization** in read-model builder: keep backbone fields, add canonical `blockers[]` / `field_key` / `state`.
- **B — Response adapter** at route only (same effect, farther from source).
- **C — Typed union** with discriminant (clearer docs, larger FE/BE churn).
- **D — No backend change** (FE-only already shipped; leaves API inconsistent).

## Chosen approach

**Option A** in `form_system_runtime_capture_read_model_service._normalize_runtime_capture_blocker_rows`.

Reasoning: one predictable public row; no invented codes; additive so older readers of `blocker_code` / `message` / `severity` / `blocks` still work; `blocks` not copied into `blockers`.

## Final representative JSON (Logo fail-closed)

```json
{
  "field_key": "root",
  "blockers": ["LOGO_NOT_OFFERABLE"],
  "state": "blocked",
  "blocker_code": "LOGO_NOT_OFFERABLE",
  "severity": "blocked",
  "message": "...",
  "blocks": ["quote_preview", "..."]
}
```

## Tests

- `pytest tests/test_form_system_runtime_capture_read_model.py` + endpoint suite (Logo normalize + HTTP contract proof)
- Vitest: `intakeV6OperatorBlockerBannerDisplay.test.ts`, `intakeV6ReviewDiagnosticEntryCount.test.ts`

## HTTP CONTRACT PROOF

Isolated TestClient route `GET .../runtime-capture-read-model` for Logo workspace:

- normalized `blockers: ["LOGO_NOT_OFFERABLE"]` once
- additive backbone fields present
- `readiness_status` remains `logo_only_candidate_not_offerable`
- quote handoff `handoff_allowed` / `can_create_internal_draft_quote` remain false

Not production proof.

## Impact

- `/modules` (Harta sistemelor): **NO SYSTEM IMPACT**
- `/governance`: **NO UPDATE REQUIRED** (Logo owner boundary unchanged; payload consistency only)

## Commit

`fix(intake): normalize runtime capture blocker contract`
