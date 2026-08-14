# Wave 4 — ProductAggregate ownership

| Claim | Actual |
|-------|--------|
| Owns selected graph | YES on workspace compose (`compose_from_product_definition`) |
| Owns component outputs | PARTIAL — materials/ops from child templates |
| Owns technical facts | YES as read model |
| Owns commercial measurements | YES for Letters CPP measurements (non-money) |
| Owns execution handoff | Indirect — `task_contract` → frozen snapshot → plan |
| Provenance | YES (warnings, explicit graph applied) |
| Duplicates PD | Compile input vs graph output — related, not identical |
| Duplicates Intake | No — consumes workspace |
| Duplicates Product System | Template-only `build()` is PASS_THROUGH of catalog |

**Classify: PARTIAL_AGGREGATE** (Letters workspace path approaches COHERENT_AGGREGATE; template-only is PASS_THROUGH; ACM Decision A avoids duplicate BOM).

**PRODUCT_AGGREGATE_OWNERSHIP = PARTIAL**
