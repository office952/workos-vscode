# 2026-07-16 — Logo-only readiness owner audit + alignment

## Owner decision (binding)

`TPL-VOLUMETRIC-LOGO_v1` remains:

- `candidate_only = true`
- `root_offerable = false`
- `owner_go_required = true`

A Logo-only / root Logo workspace must **not** report `ready_for_quote_preview`.  
Confirmed constructive-model data may make the candidate technically complete, but readiness must stay explicitly non-offerable until a separate owner GO activates a valid root product path.

No Logo root activation. Offerability policy unchanged.

## Runtime correction

`backend/services/intake_v6_workspace_service.py` — `_is_logo_only_candidate_not_offerable`:

| Before | After |
|--------|-------|
| `composition_type == "logo_only"` → cleared guard (`False`) | → keep non-offerable (`True`) |
| `TPL-VOLUMETRIC-LOGO_v1` root binding with confirmed artwork → could reach `ready_for_quote_preview` | → always `logo_only_candidate_not_offerable` |
| Structural logo-only cleared when all artwork rows confirmed (`_logo_constructive_model_confirmed`) | → constructive confirmation no longer clears the boundary |
| Helper `_logo_constructive_model_confirmed` | removed (unused) |

Letters + artwork still skip the logo-only guard (`face` role present) and continue through the canonical capture-blocker spine.

## Statuses before / after

| Scenario | Before | After | Offerable |
|----------|--------|-------|-----------|
| Logo-only, artwork unconfirmed | `logo_only_candidate_not_offerable` | `logo_only_candidate_not_offerable` | No |
| Logo root / logo-only, artwork confirmed | `ready_for_quote_preview` | `logo_only_candidate_not_offerable` | No |
| Letters + artwork (no full capture) | `runtime_capture_blocked` | `runtime_capture_blocked` | Per letters policy / capture |

UI already maps `logo_only_candidate_not_offerable` (header + commercial guard). No frontend change required.

## Test correction

`backend/tests/test_intake_v6_logo_only_readiness.py`:

1. Keep unique guard: unconfirmed logo-only → `logo_only_candidate_not_offerable`
2. Correct case 2: Logo root + confirmed artwork → `logo_only_candidate_not_offerable` (not quote-ready)
3. Replace stale case 3: letters + artwork must **not** use logo-only guard; expect `runtime_capture_blocked` (capture authoritative; no duplicate of full spine green path)

No DB/seed mutation.

## Tests run

```text
pytest tests/test_intake_v6_logo_only_readiness.py \
       tests/test_intake_v6_canonical_readiness_spine.py \
       tests/test_intake_v6_readiness_severity_channel_split.py \
       tests/test_product_template_availability.py::test_root_offerable_policy_includes_acm_excludes_logo \
       tests/test_commercial_price_proposal_linked_logo.py::test_linked_logo_template_not_root_offerable
→ 22 passed
```

Also: logo + letters policy selectors → passed.  
Pre-existing unrelated failure: `test_internal_modules_remain_component_only_non_root` (metal premount) — out of scope.

## Runtime verification

Service-level (no safe seeded HTTP workspace for Logo-only):

| Fixture | Readiness | `root_offerable` |
|---------|-----------|------------------|
| Logo root, artwork unconfirmed | `logo_only_candidate_not_offerable` | false |
| Logo root, artwork confirmed | `logo_only_candidate_not_offerable` | false |
| Letters binding + logo_only composition, confirmed | `logo_only_candidate_not_offerable` | true (letters) but readiness blocks commercial CTA via status |

Expected UI guard: existing Logo-only commercial guard / “neofertabil comercial”.

## Impact Harta sistemelor (`/modules`)

`NO NEW SYSTEM PATH` — corrected status inside existing Intake V6 / Product System candidate boundary. No modules handoff update.

## Impact Guvernanta sistemului (`/governance`)

`NO UPDATE REQUIRED` — Governance already documents Logo candidate-only / root non-offerable / owner GO. Runtime now matches that boundary at readiness.

## Commit

Isolated: readiness helper + Logo readiness tests + this worklog.  
Message: `fix(intake): keep logo readiness candidate-only`
