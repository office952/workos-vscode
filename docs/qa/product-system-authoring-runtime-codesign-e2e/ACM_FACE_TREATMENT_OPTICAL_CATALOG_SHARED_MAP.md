# ACM Face-Treatment Optical Catalog — Shared Map

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| CP0 | `ACM_FACE_TREATMENT_OPTICAL_CATALOG_CP0_FREEZE.md` |
| Allowlist | `ACM_FACE_TREATMENT_OPTICAL_CATALOG_ALLOWLIST.md` |
| Kickoff HEAD | `9bdcfaa8` |

## Agents A–G

| Agent | Scope |
|-------|--------|
| A Catalog identity | Resolution rows + statuses; no invented rates |
| B Domain / PT | Scoped optical vs illumination blockers |
| C PD / Aggregate | Project catalog map; empty treatment materials/ops |
| D Quantity / ops | Intent identity + precise blockers |
| E CPP / EIC | Scenario proofs; panel lines preserved |
| F UI | Readiness / blockers / lines_allowed / subtotal BLOCKED |
| G QA | Tests, screenshots, runtime JSON, report §§1–35 |

## Catalog resolution rows

| Need | Candidate key | Classification / status | Action | Blocker when active |
|------|---------------|-------------------------|--------|---------------------|
| Panel sheet / cut / V-groove / assembly | `acm_*` + `ACM_PANEL_CUTTING` / `ACM_V_GROOVE` / `ACM_BOXED_ASSEMBLY` | **WIRED** (panel shell — pre-existing) | Preserve | — |
| Acrylic insert ~10 mm material | `MAT-PLEXI-OPAL-10MM`, `MAT-PLEXI-TRANSP-10MM` | **KEY_STUB_NO_RATE** | STOP priced | `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` |
| Optical backing plexi (routed) | `MAT-PLEXI-OPAL-3MM` stub; letter `MAT-ACP-FATA-LITERE` | **KEY_STUB_NO_RATE** / **WRONG_PRODUCT** | STOP | `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` |
| CNC route ACP face | intent `cnc_route_acp_face` (≠ `ACM_PANEL_CUTTING`) | **GENUINELY_MISSING** | STOP | `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` |
| Cut / mount plexiglas backing | intents only | **GENUINELY_MISSING** | STOP | `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` |
| CNC insert pocket / cut insert / fit / retain | intents only | **GENUINELY_MISSING** | STOP | `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` |
| Insert adhesive / spacers | stubs / MIXED tech only | **GENUINELY_MISSING** | STOP | `FACE_TREATMENT_OPTICAL_CATALOG_MISSING` |
| Treatment LED / PSU / wiring | volumetric `MAT-LED-*` | **WRONG_PRODUCT** (letters ≠ cavity); ACP RO MISSING | STOP remap | `FACE_TREATMENT_ILLUMINATION_RATES_MISSING` |
| LIGHT-ROUTED formulas | `TPL-ACP-LIGHT-ROUTED` | **LEGACY_FORBIDDEN** | Never wire | — |

## Commercial spine (optical closure)

```text
typed PT config (finish_setup.acm_face_treatments)
  → normalize + scoped blockers
  → catalog_resolution projection (status per need)
  → PD / Aggregate (materials/ops empty until WIRED)
  → CPP/EIC gate (treatment_commercial_lines_allowed=false unless all required WIRED)
  → readiness (panel-only PASS; treatments PASS_WITH_WARNINGS / optical BLOCK)
  → UI face-treatment section (codes + subtotal BLOCKED|null)
```

## Priced emission rule

`treatment_commercial_lines_allowed = true` **only if** every required optical/illumination resolution row for the active coexistence is `WIRED` with proven owner rate + unit. This run: **false** whenever treatments are active.
