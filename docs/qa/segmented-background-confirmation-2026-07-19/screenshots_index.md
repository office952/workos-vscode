# Segmented background confirmation — screenshots

Route host (live): Intake V6 → Review → mounting / ACP section  
Component: `IntakeV6SegmentedBackgroundPanel`  
Fixture HTML (static visual proof of copy/states): `fixtures/segmented-panel-states.html`

| # | File | State | Expected |
|---|------|-------|----------|
| 0 | `00_all_states.png` | All | Full board |
| 1 | `01_proposal.png` | Propus | Title, panel list, Confirma/Respinge |
| 2 | `02_distributed.png` | Propus | Distributed graphic info |
| 3 | `03_applied_crossing.png` | Propus | Two-stage info; Confirma enabled |
| 4 | `04_cutout_blocker.png` | Propus | Blocker; Confirma disabled |
| 5 | `05_confirmed.png` | Confirmat | Confirmed banner; no actions |
| 6 | `06_reloaded.png` | Confirmat | Same IDs/order after reload |

Note: static fixture may show encoding artifacts for middle-dot; live React panel uses UTF-8 source.
