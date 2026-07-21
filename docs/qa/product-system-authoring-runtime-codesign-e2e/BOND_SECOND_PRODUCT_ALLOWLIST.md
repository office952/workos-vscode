# Bond Second Product Configuration — Allowlist (STOP gate)

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `1b1b333c` (reconfirmed) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Gate | **STOP before create** — near-identity inventory required |
| Subject | Second real product: Bond casetat cu litere / logo volumetric |

## Commit sequence (planned after owner GO past STOP)

| # | Message | Status this run |
|---|---------|-----------------|
| 1 | `feat: boxed bond product identity and composition` | **SKIPPED** (STOP) |
| 2 | `feat: bond and frame component contracts` | **SKIPPED** (STOP) |
| 3 | `feat: connect volumetric letters or logo reuse` | **SKIPPED** (STOP) |
| 4 | `feat: compile aggregate quantities and readiness` | **SKIPPED** (STOP) |
| 5 | `test: second product configuration and reuse boundaries` | **SKIPPED** (STOP) |
| 6 | `docs(qa): second-product and generalization evidence` | **THIS RUN** (inventory + STOP report only) |

## Allowed paths (this STOP package)

### Docs / QA / worklog

- `docs/qa/product-system-authoring-runtime-codesign-e2e/BOND_SECOND_PRODUCT_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/bond_second_product_*`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (additive VL closure + second-product section only)

## Forbidden (unchanged)

- Creating / renaming / activating Bond-near templates without owner canonical GO
- Publishing any product; auto-activating inactive components
- Touching `TPL-VOLUMETRIC-LETTERS_v2` beyond short worklog closure pointer
- Schema migrations / ProductInstance / ComponentInstance / ComponentTemplate tables
- SVG/DWG/DXF / artwork analysis / Build 2 / Execution materialization
- Pricing redesign / VL Aluminiu formula changes
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
