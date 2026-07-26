# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Risk Register

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| R-SEED-01 | Seed realign breaks tests expecting ops on `comp_logo_face::` | Medium | Update logo op tests to `comp_logo_finish::` |
| R-SEED-02 | Re-seed required in dev DB | Low | Idempotent seed script; document in worklog |
| R-MAP-01 | mapping_only excluded breaks template-only preview | Low | Scope guard to linked logo workspace + artwork concepts |
| R-SEG-01 | Cross-segment dedupe | Critical | Identity key includes segment_key; explicit tests |
| R-FACE-01 | Face artwork removed but plexi path needs face material | Low | Retain `logo_face_material` + CNC on face |
| R-QTY-01 | Quantity formulas altered | Critical | Row filter only — forbidden |
| R-EIC-01 | EIC used to hide duplicates | High | Out of scope |
| R-RATE-01 | 35 RON/m² enabled in same build | Critical | Forbidden; assert blockers remain |
| R-REG-01 | Letters aggregate regression | Medium | Letters-only test batch |
| R-BOM-01 | BOM guard without seed still leaves face ops | High | Option A required, not optional |
