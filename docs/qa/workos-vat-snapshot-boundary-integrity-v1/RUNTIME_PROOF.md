# RUNTIME_PROOF

| Gate | Result |
|------|--------|
| DEMO_DB_ONLY / isolated test DB for mutating proof | YES — pytest `volumetric_v2_db` fixture (not Owner `backend/dev.db`) |
| OWNER_DEV_DB_MUTATIONS | 0 |
| Scenario A (Settings 21→19 post-freeze) | PASS (`test_vat_snapshot_boundary_integrity_v1.py`) |
| Fail-closed missing provenance | PASS |
| Live Settings remaining on offer/pricing-review | NONE (`get_default_vat_pct` removed from both) |

UI: Settings VAT copy updated to describe freeze boundary for offer review + order (not over-claiming document path).
