# Intake V6 — Return/Cant Readiness + Single Final Confirmation V1

| File | URL | Workspace | Step | State | Click path | Expected | Proves |
|------|-----|-----------|------|-------|------------|----------|--------|
| 01_three_step_navigation.png | `/intake-v6/22ef834d…/operator` | IV6-189D2F12 | Pas 1 | Default load | Open operator route | Straturi · Configurare · Confirmare visible | Three-step flow restored (DEC-CDRC-03) |
| 02_step2_cant_60mm_no_false_warning.png | same | same | Pas 2 | Configurare top | Progress → Configurare | 60 mm + Alb shown; no false cant missing | Valid persisted cant accepted (DEC-CDRC-01) |
| 03_step2_print_laminate_no_false_warning.png | same | same | Pas 2 | Mid scroll | Scroll to artwork | print + laminare; no artwork unconfirmed from flag | Per-row confirmed ignored when values valid (DEC-CDRC-02) |
| 04_step2_real_blocker_only.png | same | same | Pas 2 | Footer area | Scroll bottom | Only genuine unresolved warnings | Real blockers preserved |
| 05_step3_summary_collapsed.png | same | same | Pas 3 | Confirmare | Progress → Confirmare | Compact summary collapsed by default | Pas 3 separate; summary policy |
| 06_step3_summary_expanded.png | same | same | Pas 3 | Summary open | Toggle Rezumat configuratie | Dimensions, layers, finishes visible | Summary expands without raw codes |
| 07_step3_final_confirmation.png | same | same | Pas 3 | Footer | Scroll bottom | Single final confirmation checkbox | `internal_draft_quote_confconfirmed` boundary (DEC-CDRC-04) |
| 08_step3_blocked_real_missing_value.png | same | same | Pas 3 | Summary collapsed | Collapse summary | Final action blocked with real reason | No auto-confirm; real blockers remain |
| 09_technical_details_collapsed.png | same | same | Pas 3 | Technical accordion | Expand summary → Detalii tehnice collapsed | Secondary technical section | Technical diagnostics preserved, demoted |
| 10_technical_details_expanded.png | same | same | Pas 3 | Technical open | Expand Detalii tehnice | Raw codes / mapper state visible | Auditability preserved (HIDDEN_FROM_NORMAL_UI) |
