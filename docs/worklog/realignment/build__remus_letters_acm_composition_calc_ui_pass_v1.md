# Build — Remus Letters↔ACM composition calc UI PASS v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Verdict** | **PASS** |
| **Workspace** | `IV6-B4011E1D` / `e64ab257-a270-4774-bc34-451cf48d8113` |
| **Fixture** | `test-bond-litere.svg` |

## Claim (falsifiable)

Intake V6 Remus panou+litere: Step 1 shows 2 layers / `letters_plus_support`; after property confirm, priced dry-run includes VL + `acm_*` + `letters_acm_conn_*`.

## Evidence

- Screenshots: `docs/worklog/realignment/audit_assets/remus_letters_acm_composition_calc_ui_v1/screenshots/`
- Verdict: `.../verdict.json`
- Dry-run: `.../dry_run.json`
- E2E: `frontend/e2e/intake-v6-remus-letters-acm-composition-calc-ui.spec.ts` — **1 passed**

### Dry-run codes (excerpt)

- VL: `debitare_fata`, `modelare_cant_aluminiu`, `sistem_led_module`, …
- Bond: `acm_panel_cut`, `acm_v_groove`, `acm_boxed_assembly`, …
- Contract: all 7 `letters_acm_conn_*` (șablon, forex, electric, cablu, test, attach, pack)

`applied_content=letters`, `composition_type=letters_plus_support`.

## Notes

UI color-card path often drops stroke-only Alucobond; evidence path re-POSTs analysis-bundle with both Corel layers after UI upload, then confirms composition + finish.
