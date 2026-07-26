# AI_OPERATIONAL_DEFAULTS_V1 — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `aa0f8956` |
| Final HEAD | `19fc3c6a` |
| Verdict | **PASS_WITH_WARNINGS** |
| Evidence | `docs/qa/ai-operational-defaults-v1/` |
| API schema | **1.2.0** (`ai_decisions[]`, activation_status) |
| DB migration | **NU** |
| Push / PR | **NU** |

## 1. Verdict by axis

| Axis | Result |
|------|--------|
| AI decision contract | PASS — typed registry + override JSON |
| Packaging | PASS — S/M/L + fragile; demotes AMBALARE |
| Electrical | PASS — min + per PSU; no minutes |
| LED | PASS — per module; catalog beats AI when rate exists |
| Labor fallback | PASS_WITH_WARNINGS — eligible only; PREPRESS skipped |
| Configurability | PASS — PUT/DELETE + Studio inputs |
| Precedence | PASS — MEASURED > OWNER > CATALOG > AI > LEGACY |
| Readiness | PASS — ACTIVE_WITH_AI_DEFAULTS / WARNINGS / BLOCKED |
| Activation | PASS_WITH_WARNINGS — readiness eligible; lifecycle publish not auto |
| CPP | PASS — lines same; `ambalare` demoted from blocked |
| EIC | PASS — rules/provenance unchanged |
| UI | PASS — Decizii operaționale AI + screenshots |
| Regression | PASS — ACM 5/0; treatments blocked; no catalog write |

## 2. Executive truth (RO)

Lipsa unui tarif „perfect” nu mai blochează automat template-ul. AI decide default-uri operaționale (ambalare, electric, LED, manoperă shell ACM), le marchează clar, le face configurabile și lasă măsurătorile/owner-ul să le înlocuiască. Timpul nu este baza de cost. Blocare rămâne doar pentru imposibilități reale (ex. tratamente ACM).

## 3. Repo / branch / HEADs / dirty tree

- Repo: `C:\w\psiso`
- Branch: `feature/product-system-active-path-isolation-v1`
- Kickoff: `aa0f8956`
- Final HEAD: `19fc3c6a`
- Commits: `72dfecb4` → `6d8e3d60` → `0a8cec13` → `b8e678b6` → `19fc3c6a`
- Dirty tree: large unrelated set — only allowlist files touched

## 4. Owner strategy readback

```text
Lipsa adevărului perfect → AI decision configurabilă → activare controlată → calibrare ulterioară
```

Accepted. Implemented without waiting for productivity/time owner numbers.

## 5. Runtime truth

Proof `:8020`. `:8000` ghost. FE `:3000` serves schema 1.2.0. See `RUNTIME_API_TRUTH.md`.

## 6–9. Plan / map / agents / CP0

CP0 freeze + allowlist + decision table committed under `docs/qa/ai-operational-defaults-v1/`. Shared map: `COMPOUND_ENGINEERING_MAP.md`.

## 10. Artificial blocker inventory

See `BLOCKER_DEMOTION_INVENTORY.md`.

## 11–13. Contract / precedence / decision table

Application-layer Python registry (`backend/data/ai_operational_defaults_v1.py`). No Alembic. Initial numbers in `AI_OPERATIONAL_DEFAULTS_V1_DECISION_TABLE.md`.

## 14–17. Domain defaults

| Domain | Key IDs | Basis |
|--------|---------|-------|
| Packaging | AI_PACK_* / AI_PACK_PRODUCT_BAND | face_area bands + fragile |
| Electrical | AI_ELEC_MIN_PRODUCT, AI_ELEC_PER_PSU | product min + PSU |
| LED | AI_LED_PER_MODULE | module_count × rate |
| ACM labor | AI_ACM_PANEL_LABOR_M2 | panel_area_m2 × rate (shell) |
| PREPRESS | — | no AI invent |

## 18. No-time-primary proof

No formula requires minutes/hours/worker productivity for activation. `led_assembly_time` unbound. Calibration hooks include `observed_time` only as future metadata.

## 19–21. Configurability / overrides

JSON override store + API PUT/DELETE. UI Salvează/Reset. Catalog/owner/measured beat AI in resolution labels.

## 22–24. Readiness / templates / real blockers

| Template | Status |
|----------|--------|
| VL | ACTIVE_WITH_AI_DEFAULTS |
| Logo | ACTIVE_WITH_AI_DEFAULTS |
| ACM | ACTIVE_WITH_WARNINGS (treatment blocker retained) |
| Volum Aluminiu | ACTIVE_WITH_AI_DEFAULTS (packaging AI; catalog gaps remain) |

Lifecycle publication not auto-flipped — readiness state is the V1 deliverable.

## 25–26. CPP / EIC

CPP line codes unchanged; VL blocked set lost `ambalare` only. EIC identical to Labor Closure dumps.

## 27. UI / screenshots

See `SCREENSHOT_MATRIX.md` (7 evidence shots).

## 28. Tests

```text
pytest tests/test_ai_operational_defaults.py tests/test_template_labor_recipe.py
      tests/test_template_pricing_recipe.py tests/test_template_labor_formula_truth.py
→ 23 passed
```

## 29–33. Runtime evidence / files / commits / worklog / dirty tree

Runtime JSON under `runtime/`. Worklog append: `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`. Unrelated dirty paths untouched.

## 34. Remaining warnings

- Calibration samples absent → PASS_WITH_WARNINGS
- Catalog rate-basis mismatch warnings still noisy
- PREPRESS OPERATION_ONLY
- Volum Aluminiu bonding/paint still MISSING_CATALOG_RATE
- Template lifecycle publish still separate gate
- `:8000` ghost environment

## 35. Calibration roadmap

Hooks present: observed_actual_cost, operation_count, observed_time, variance, sample_count. No analytics UI in V1.

## 36. Next recommended build (do not auto-execute)

**TEMPLATE_ACTIVATION_V1** — turn ACTIVE_WITH_AI_DEFAULTS readiness into controlled lifecycle publication for VL/Logo, with ACM still controlled acceptance.

Alternates: `AI_OPERATIONAL_DEFAULTS_V1_CLOSURE`, `CNC_MACHINE_SERVICE_MATRIX_V1`, `ACM_PRICED_ACTIVATION_V1`.

## 37. Dead pieces

None introduced. Override file empty by default. No dual registry.

## 38. Method

Plan Mode → CP0 freeze → application registry (no migration) → demote artificial blockers → Studio UI → CPP/EIC compare → screenshots → commits.

## 39. Părerea sinceră ca agent

| Question | Answer |
|----------|--------|
| Artificial blockers removed? | Yes for packaging/eligible labor; PREPRESS/treatments kept |
| Values reasonable? | Conservative mid-band; not cheap, not absurd |
| Visible + configurable? | Yes |
| Avoided time-primary? | Yes |
| Owner/measured replace AI? | Precedence + override path yes; measured UI not full yet |
| Real blocker wrongly removed? | No — ACM treatments retained |
| CPP/EIC coherent? | Yes |
| Templates more operational? | Yes at readiness layer |
| UI in 10s? | Yes |
| Fragile? | rate-basis noise; publish gate; calibration empty |
| Activate next? | TEMPLATE_ACTIVATION_V1 |

## 40. Roadmap awareness

Inventory live · catalogs reusable-rate authority · Product System owns recipes · AI fills operational gaps · time calibration-only · ACM controlled · dual-select HOLD · no Execution · no artwork · no Build 2 · mobile final-final.

## 41. Direction score

| Axis | Score |
|------|------:|
| Activation path | 78% |
| AI decision quality | 80% |
| Configurability | 85% |
| Pricing coherence | 82% |
| Blocker reduction | 75% |
| Template readiness | 80% |
| CPP/EIC safety | 90% |
| Calibration readiness | 55% |
| **Overall direction** | **78/100%** |
