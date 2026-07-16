# 2026-07-16 — Logo-only readiness owner audit

## Scope

Audit untracked `backend/tests/test_intake_v6_logo_only_readiness.py`.  
No production changes. No seed/DB mutation. No test commit without owner GO.

## Gate

- HEAD: `1351d541377f73fcfb80b4e808750fe4dee1f4a5`
- branch: `feature/product-system-active-path-isolation-v1`
- test status: **untracked**

## Classification (agent)

`OWNER_PRODUCT_DECISION_REQUIRED`

(Secondary: third case is stale vs capture-blocker spine → would need `CORRECT_TEST_ONLY` if package is kept.)

## Test intent

Unit tests of private helper `_derive_readiness_status` (no HTTP, no DB):

| Case | Binding | Layers / finishes | Expected readiness |
|------|---------|-------------------|--------------------|
| 1 | `TPL-VOLUMETRIC-LETTERS_v2` | only `printed_artwork`; artwork **unconfirmed** | `logo_only_candidate_not_offerable` |
| 2 | `TPL-VOLUMETRIC-LOGO_v1` | only `printed_artwork`; artwork **confirmed** | `ready_for_quote_preview` |
| 3 | `TPL-VOLUMETRIC-LETTERS_v2` | face + artwork confirmed | `ready_for_quote_preview` |

**“Logo-only readiness” in product terms:** workspace has artwork/logo layers but no letter (`face`) roles — treated as logo-only candidate until artwork finishes are confirmed (“constructive model”).

## Runtime evidence

Tracked in `backend/services/intake_v6_workspace_service.py`:

- `_is_logo_only_candidate_not_offerable` → returns `logo_only_candidate_not_offerable` when no letter roles, has logo/artwork roles, artwork finish rows exist, and **not** all artwork finishes confirmed.
- Once `_logo_constructive_model_confirmed` is true, that guard clears and readiness proceeds to capture-blocker merge (`intake_v6_canonical_readiness_service`).
- UI already surfaces the status (`intake-v6-header-logo-only-guard`, Review commercial guards).
- Template policy (`template_usage_mode_policy.py`): `TPL-VOLUMETRIC-LOGO_v1` is **`root_offerable=False`**, **`candidate_only=True`**, **`owner_go_required=True`**.
- Frontend active scope: `isOwnerValidActiveTemplate("TPL-VOLUMETRIC-LOGO_v1") === false`.
- Quote create still gated by `quote_offerable` / `_resolve_offerable_template_code_or_raise` (separate from readiness string).

## Boundary analysis

| Question | Answer |
|----------|--------|
| Active Product System root path? | **No** — Logo is linked child / candidate, not owner-valid root |
| Bypass PD/Aggregate? | Test does not exercise PD/Aggregate; only readiness helper |
| Accidentally activate broader family? | Case 2 readiness=`ready_for_quote_preview` on LOGO root binding **looks** offerable at readiness layer while policy forbids root offer — soft conflict |
| ACM/Logo scope guards? | Does not activate ACM; Logo root activation still blocked at availability/quote layer |
| Regression guard for existing behavior? | **Case 1 yes**; Case 2 documents constructive-model escape; Case 3 stale |

## Isolated test result

```text
npx/pytest: tests/test_intake_v6_logo_only_readiness.py
2 passed, 1 failed
FAILED test_letters_with_artwork_can_still_be_quote_ready_when_confirmed
  expected ready_for_quote_preview
  got runtime_capture_blocked
```

No DB/seed used.

## Duplicate / conflict

- No other backend test asserts `logo_only_candidate_not_offerable` (unique coverage for case 1).
- Case 3 overlaps intent of `test_intake_v6_canonical_readiness_spine.py` and is **outdated** after capture-blocker merge.
- Case 2 vs contracts: UI inventory / availability say logo-only stays not-offerable; runtime clears status when finishes confirmed — **truth conflict for owner**.

## Owner-friendly decision

### Ce testeaza

Daca readiness blocheaza logo-only pana la confirmarea finish-urilor artwork, si ce status iese dupa confirmare (inclusiv pe binding `TPL-VOLUMETRIC-LOGO_v1`).

### Ce produs/flow ar activa

Nu activeaza un template nou in Product System. Documenteaza / blocheaza path-ul Intake V6 „doar logo” (candidate). Cazul 2 sugereaza ca dupa confirmare constructive model, readiness poate deveni `ready_for_quote_preview` pe root Logo — **fara** a face Logo `root_offerable` in policy.

### Este deja comportament real?

Da pentru helper-ul `_derive_readiness_status` (cazurile 1–2 trec).  
Nu pentru cazul 3 (acum `runtime_capture_blocked`).  
Ofertabilitatea reala Logo root ramane blocata de availability/policy.

### Ce se intampla daca il pastram

Pastram un regression guard util (cazul 1), dar comitem un suite care **esueaza** (cazul 3) si care **normalizeaza** readiness quote-ready pe LOGO_v1 (cazul 2) fara decizie de produs.

### Ce se intampla daca il stergem

Pierdem singura acoperire explicita pentru `logo_only_candidate_not_offerable`. Riscul: regresii pe guard-ul logo-only.

### Recomandarea agentului

`DECIDEM PRODUSUL MAI INTAI` — apoi:

1. Daca Logo root **nu** poate fi quote-ready: pastreaza cazul 1; rescrie cazul 2 sa astepte `logo_only_candidate_not_offerable` sau alt status non-offerable; sterge/corecteaza cazul 3 pentru capture blockers (`CORRECT_TEST_ONLY`).
2. Daca constructive model **permite** readiness quote-ready pe LOGO (oferta tot blocata la availability): pastreaza 1+2; corecteaza doar cazul 3.
3. Pana la decizie: **`PARCAM`** — nu comite testul.

**Owner answer:** `PASTRAM SI COMITEM` · `CORECTAM DOAR TESTUL` · `PARCAM` · `STERGEM` · `DECIDEM PRODUSUL MAI INTAI`

## Impact

- `/modules`: **FUTURE PATH OWNER GATE** (nu e sistem produs nou; implica path candidate Logo)
- `/governance`: nu actualiza pana la decizia owner — afecteaza potential activation boundary / owner GO pe Logo

## Commit

`NO TEST COMMIT — WAITING FOR OWNER DECISION`  
Docs-only audit commit optional for this worklog.
