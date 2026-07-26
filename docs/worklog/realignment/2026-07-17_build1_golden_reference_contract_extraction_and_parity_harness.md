# Build 1 — Golden Reference Contract Extraction and Parity Harness

| Field | Value |
|-------|--------|
| Task | BUILD1_GOLDEN_PARITY |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Remote | `https://github.com/office952/workos-vscode.git` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `163f35f` |
| End HEAD | `9d56b19` |
| Mode | IMPLEMENTATION WITH OWNER GO — Build 1 only |
| Commit | `9d56b19` — exact-path isolated |

## Objective

Executable golden inventory + ownership map + parity harness for SVG / formulas / PD / Aggregate / CPP without changing operator behavior, formulas, prices, or schema.

## Scope

**In:** extract, label, version, trace, compare, test, docs, worklog, isolated commit  
**Out:** subset UI, Gates A–D, SVG redesign, ACM/Logo sold activation, freeze/order/tasks, migrations, seeds, Build 2+

## Agents (Compound Engineering)

| Agent | Mode | Result |
|-------|------|--------|
| A Golden UI | read-only | Review/layers/form inventory via prior evidence + review contract fixture |
| B SVG | read-only → harness | nest2 facts 6/5/36/~5087×600; ACM absent |
| C Formula | harness | `build_quote_geometry_from_analysis` exact match to expect |
| D Product System | ownership map | dossier/mini-module/form contracts reused |
| E PD | pytest + live | selected modules frozen; geometry from fixture payload |
| F Aggregate | fixture + live | seed thin; live historical emits adhesive+bonding |
| G CPP | disposable + live | exact fingerprints; dry-run no-write |
| H Adversarial | review | see findings below |

## Method

1. Parallel research (existing probes/evidence/tests)  
2. Single synthesis → fixtures under `backend/tests/fixtures/intake_v6_golden_gradi/`  
3. Harness service (compare-only)  
4. Pytest + Vitest  
5. Live read-only probes against historical WS `4888fddb-…` on `:8001`  
6. One fix pass (expect alignment to HEAD; fixture vs live split)  
7. Worklog + isolated commit  

## Golden / SVG fixtures

- SVG: `gradi-curat.svg` hash `593c4d43…6cf1` (27173 bytes)  
- Historical WS (read-only): `4888fddb-5d9f-46cb-9bcc-5dd3ed1263b1` / `IV6-C8066690`  
- Disposable WS: created only inside pytest (`IV6-GOLD-*`)  

## Parity results

| Layer | Result |
|-------|--------|
| SVG facts | PASS (pytest + vitest nest2) |
| Formula / quote_geometry | PASS (21.1675 ml perimeter from analysis fixture) |
| Review contract | PASS (captured expect) |
| PD modules + geometry | PASS (fixture disposable) |
| Aggregate fixture DB | PASS (thin seed anchors) |
| Aggregate live historical | PASS (17 mats incl. adhesive; bonding present) |
| CPP disposable | PASS (exact fingerprint; debitare_fata=21.1675) |
| CPP live historical | PASS (exact fingerprint; debitare_fata=20.9727) |
| Dry-run no-write | PASS |
| Schema/migration | none introduced |

## Geometry drift guard (adversarial)

| Source | letter_perimeter_m |
|--------|--------------------|
| Analysis fixture rebuild | **21.1675** |
| Live historical WS dry-run | **20.9727** |

Do **not** mutate historical WS. Build 1 freezes both fingerprints and asserts the delta remains visible.

## Adversarial findings

1. `volumetric_v2_db` seed Aggregate ≠ live Aggregate (adhesive missing in seed) — documented, not “fixed” via seed change.  
2. Historical perimeter ≠ analysis-fixture rebuild — drift guard test.  
3. Disposable CPP line set thinner than live (LED/PSU present live) — live fingerprint is full-set authority.  
4. Soft defaults (`illuminated`, `mounting_template_enabled`) still golden UI behavior — not changed.  
5. Pricing Registry UI (`/inventory/pricing`) ≠ CPP money authority (`commercial_rules_volumetric_v2`) — confirmed; no 7I activation.  
6. No formula/price code changed.  

## Fix pass (single)

- Split Aggregate expects into fixture_db vs live_runtime  
- Freeze PD selected modules to current HEAD (8 modules)  
- Add live read-only CPP/Aggregate parity tests  
- Geometry drift guard test  

## UI proof

Fresh 15-step Playwright disposable walkthrough **not re-executed** in this Build 1 write pass.  
Prior same-day evidence retained: `docs/audits/_evidence/2026-07-17_intake_v6_gradi_curat/`.  
Runtime live read-only PD/Aggregate/CPP proven against historical WS on `:8001`.

## Tests run

```text
backend: pytest tests/test_intake_v6_golden_parity_harness.py → 18 passed, 1 skipped
frontend: vitest src/lib/intakeV6/goldenParity/goldenSvgFacts.test.ts → 2 passed
```

## Runtime

| Service | Status |
|---------|--------|
| Frontend `:3000` | assumed available (not required for harness unit tests) |
| Backend `:8001` | UP — live Aggregate/CPP parity used |

## Owner gates remaining

| Gate | Note |
|------|------|
| Build 2 GO | Full-product reproduction from contracts — separate |
| Historical perimeter drift | Owner may decide whether to re-baseline from disposable re-upload (without mutating `4888fddb`) |
| Seed vs live Aggregate gap | Optional later seed enrichment — **not** Build 1 |
| Gates A–D | After modular scope Build 3 |

## Explicit exclusions honored

No subset UI, no Gates A–D impl, no SVG redesign, no ACM/Logo sold activation, no quote freeze/order/tasks, no schema/migration/seed, no `/price` writes, no historical WS mutation, no unrelated dirty staging.

## Files modified (Build 1)

- `backend/services/intake_v6_golden_parity_harness.py`
- `backend/tests/test_intake_v6_golden_parity_harness.py`
- `backend/tests/fixtures/intake_v6_golden_gradi/*`
- `frontend/src/lib/intakeV6/goldenParity/*`
- `docs/architecture/product-system/INTAKE_V6_GOLDEN_OWNERSHIP_MAP.md`
- `docs/worklog/realignment/2026-07-17_build1_golden_reference_contract_extraction_and_parity_harness.md`

## Next safe step

Owner evaluates Build 1 parity proof → separate GO for **Build 2** (full-product reproduction from contracts). Do not start subset isolation.

## Verdict

`BUILD1_GOLDEN_PARITY_COMPLETE_WITH_GUARDS`

**Cat sunt in directia stabilita: 88/100%**
