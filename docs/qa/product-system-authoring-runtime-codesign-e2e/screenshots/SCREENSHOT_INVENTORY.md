# Screenshot inventory — Agent C (CP-G / CP-H)

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| FE | Canonical `3000` (proxy→8001 stale); completion capture on `3020` with `BACKEND_PORT=8000` |
| BE publication APIs | Present on **8000**; **absent on stale 8001** (404) |
| FE→API | `3000` publication → **404 ENVIRONMENT_FAILURE**; `3020`→8000 → **200** |
| Pack | Completion gate improved Lifecycle panels — see below |

## Figma exports (file `0CDPIuqoaZ1OQgNnvNyl1F`)

| # | File | Node | Note |
|---|------|------|------|
| F1 | `figma_01_confirmare_66-2.png` | `66:2` | Intake Confirmare FINAL |
| F2 | `figma_02_ps_shell_91-3.png` | `91:3` | PS shell (created) |
| F3 | `figma_03_contracts_91-12.png` | `91:12` | Contracts frame (created) |
| F4 | `figma_04_dossier_91-21.png` | `91:21` | Dossier frame (created) |
| F5 | `figma_05_publication_91-36.png` | `91:36` | Publication states (created) |
| F6 | `figma_06_readiness_91-60.png` | `91:60` | Readiness PASS/BLOCKED (created) |
| F7 | `figma_07_pinfooter_67-18.png` | `67:18` | PinFooter pattern |
| F8 | `figma_08_configurare_64-2.png` | `64:2` | Configurare Finisaje |
| F9 | `figma_09_iluminare_65-2.png` | `65:2` | Iluminare |
| F10 | `figma_10_montaj_65-106.png` | `65:106` | Montaj |

## Live UI captures (Playwright + browser)

| # | File | Surface | Status |
|---|------|---------|--------|
| U1 | `ui_01_product_system_catalog.png` | Product System catalog | **OK** |
| U2 | `ui_02_template_detail_volumetric.png` | VL detail Prezentare | **OK** |
| U3 | `ui_03_template_lifecycle_tab.png` | Lifecycle + mounted panels | **OK** (completion gate) |
| U4 | `ui_04_publication_panel_lifecycle.png` | Publication on Lifecycle | **OK** (was MISSING_DOM) |
| U5 | `ui_05_readiness_panel_lifecycle.png` | Readiness dual axes on Lifecycle | **OK** (was MISSING_DOM) |
| U6 | `figma_91_3_template_authoring_shell.png` / `figma_91_36_*` / `figma_91_60_*` | Figma compare frames | **OK** PROPOSED |
| U7 | `ui_07_template_dossier_tab.png` | Template Dossier tab | **OK** |
| U8 | `ui_08_blueprint_dossier_studio.png` | Dossier studio | **OK** |
| U9 | `ui_09_dossier_sticky_footer.png` | Sticky footer | **OK** |
| U10 | `ui_10_intake_confirmare.png` | Misnamed — Configurare step | **OK capture / wrong label** (see U20/U21) |
| U11 | `ui_11_intake_operator_shell.png` | Operator shell bootstrap | **OK** |
| U17 | `ui_17_dossier_publication_panel.png` | Publication panel on dossier | **OK UI / ENVIRONMENT_FAILURE API 404** |
| U18 | `ui_18_dossier_readiness_panel.png` | Readiness panel on dossier | **OK UI / ENVIRONMENT_FAILURE API 404** |
| U19 | `ui_19_dossier_fullpage.png` | Dossier full | **OK** |
| U20 | `ui_20_intake_configurare_fixture.png` | IV6-DB2F86B7 Configurare | **OK** |
| U21 | `ui_21_intake_confirmare_step.png` | Confirmare finală (blocked honest) | **OK** |

## Missing vs requested maximal pack

| Requested | Result |
|-----------|--------|
| Publication panel states (DRAFT…PUBLISHED) | Panels render; live state load **404** via FE proxy — cannot honestly show lifecycle badges from API |
| Readiness BLOCKED with aluminiu finding | Panel present; static check **404** on FE path (BE8000 alone returns BLOCKED) |
| Catalog detail publication | **Not wired** into `ProductSystemTemplateDetailPanel` (allowlist stop — do not edit foreign detail panel / dirty `ProductSystem.tsx` inseparably) |
| Named pack items 1–22 | **Undefined** in owner docs — not claimed |

## Capture scripts

- `runtime/capture_ui_screenshots.mjs`
- `runtime/capture_ui_screenshots_pass2.mjs`
