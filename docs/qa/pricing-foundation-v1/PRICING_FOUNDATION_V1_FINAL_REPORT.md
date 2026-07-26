# PRICING_FOUNDATION_V1 — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Kickoff HEAD | `46c22c16` |
| Final HEAD | `docs commit` (this docs land) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Verdict | **PASS_WITH_WARNINGS** |
| Screenshots | `docs/qa/pricing-foundation-v1/screenshots/` |

## 1. Verdict

| Axis | Result |
|------|--------|
| Inventory | PASS — preserved, 64 materials |
| Material classification | PASS — Plăci 16 / Role 14 / Cerneală 2 / Altele 32 |
| Stock semantics | PASS — null → Stoc neurmărit; Critice = 0 |
| Material pricing view | PASS — Cost achiziție label |
| Machine operations | PASS — CNC mecanic distinct |
| CNC laser | PASS_WITH_WARNINGS — distinguishable; often missing_price |
| Labor/services | PASS — separate catalog view |
| Naming | PASS — display-only |
| API compatibility | PASS — additive fields; legacy `pricing_kind` kept |
| UI | PASS — typed catalog chips |
| Regression ACM 5/0 | PASS — coverage unchanged |
| ACM freeze | PASS — KEEP_DRAFT; no wiring |

## 2. Executive truth (RO)

Inventarul rămâne viu. Taburile Plăci/Role nu mai depind de ID-uri mock. Stocul `null` nu mai e Epuizat. Pricing Registry are filtre typed: materiale / operații utilaje / manoperă+servicii, cu etichete Cost achiziție vs Rată calcul. Mismatch-urile rate_basis sunt detectate (FE + BE), fără rescriere. ACM rămâne înghețat. Preturi Template-uri = următorul build.

## 3. Repo / HEAD

| Item | Value |
|------|--------|
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff | `46c22c16` |
| Code commits | `037f08ad` inventory · `5a4cb359` typed catalog · `7826e500` tests · docs SHA = this commit |
| Dirty tree | Pre-existing non-allowlist paths left untouched |

## 4–5. Audit + owner decision

Accepted Integration Audit. Owner APPROVE Hybrid Option C. Implemented only PRICING_FOUNDATION_V1.

## 6–9. Plan / Compound / Agents / CP0

CP0 freeze: `PRICING_FOUNDATION_V1_CP0_FREEZE.md`  
Allowlist: `PRICING_FOUNDATION_V1_ALLOWLIST.md`  
Shared map: `PRICING_FOUNDATION_V1_SHARED_MAP.md`

## 10–12. Inventory

- Classification: `inventoryMaterialClassification.ts` from live `category`/`unit`/`code`
- Stock: `untracked` for null; KPI Critice/Epuizate excludes untracked
- Info banner: untracked count + missing purchase cost count
- Materials without price remain visible with “Preț lipsă”

## 13–20. Pricing typed catalog

- Backend: `pricing_typed_catalog.py` + enrich in `pricing_registry_service.py`
- Frontend fallback mirrors classification if API not yet reloaded
- Catalog chips: Preturi materiale / Operații utilaje / Manoperă și servicii
- Cost labels: Cost achiziție / Rată calcul
- CNC mechanical vs laser via `machine_family`

## 21. Rate-basis mismatches (detect only)

Schema columns: `rate_per_hour`, `rate_per_linear_meter` only.  
Bases `per_square_meter` / `per_piece` with values in linear column → flag.  
Affected codes (from live admin rates audit):  
`ACM_BOXED_ASSEMBLY`, `ELECTRICAL_WIRING`, `FACE_VINYL_APPLICATION_LABOR`, `LAMINATION`, `LARGE_FORMAT_PRINT`, `LED_ASSEMBLY`, `PACKAGING`, `PREPRESS`, `SITE_INSTALLATION_STANDARD`, `VINYL_APPLICATION`.  
No value rewrite.

## 22–26. Compatibility + counts

- ACM registry items: **5** (unchanged values 15 / 5 / 15 / 1.5 / 3)
- VL registry items: **42** (38 confirmed / 4 missing)
- Inventory materials: **64**
- Tests: pytest typed catalog 9 PASS; vitest 28 PASS

## 27–28. Product System / ACM freeze

PS still links to Pricing Registry. No Preturi Template-uri surface.  
ACM KEEP_DRAFT; treatment commercial untouched; XOR untouched; dual-select HOLD.

## 29. Files changed (allowlist)

See git commits. Key: inventory classification + stock; pricing typed catalog BE/FE; tests; docs/qa/pricing-foundation-v1.

## 30–32. Commits / worklog / dirty tree

| SHA | Message |
|-----|---------|
| `037f08ad` | `fix(inventory): align live material categories and stock semantics` |
| `5a4cb359` | `feat(pricing): classify pricing records into typed catalog views` |
| `7826e500` | `test(pricing): prove inventory preservation and pricing compatibility` |
| *(this)* | `docs(qa): finalize Pricing Foundation V1 evidence` |

Worklog section `PRICING FOUNDATION V1` appended to canonical realignment worklog. Outside-allowlist dirty paths untouched. No push / no PR.

## 33. Remaining warnings

- Live uvicorn may need restart to emit BE additive fields (FE fallback active)
- Unknown workcenter codes stay in labor/services fallback
- CNC matrix not implemented (honest)
- Markup policies empty

## 34. Next build

**TEMPLATE_PRICING_STUDIO_V1** — Product System → Preturi Template-uri (recipe composition only).

## 35–39. Method / opinion / roadmap / scores

Inventory honest: yes. Materials available: yes. Null stock correct: yes.  
10s distinguish materials/ops/labor: yes. Records preserved: yes.  
Purchase vs commercial clearer: yes (labels). CNC matrix not pretended: yes.  
ACM frozen: yes. Ready for Preturi Template-uri: foundation yes.

Direction overall: **78/100** (Inventory truth 90 · stock 92 · material pricing 80 · machine ops 75 · labor/services 72 · naming 70 · compatibility 88 · UI 85 · studio readiness 70 · ACM resumability 35).
