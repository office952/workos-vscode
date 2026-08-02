# F5 functional proof (independent)

Re-ran `test_actual_cost_coverage_v1` + F4 + profitability + post_job: **21 PASS** with `-W error::RuntimeWarning` (incl. readiness permission test).

Proven: multi-material, scrap, partial/full return, freeze, cross-job, closed-job 409 on issue/return/scrap, reopen→allow, margin unavailable while reopened, reclose restores, categories machine N/A + other_direct N/A, BOM/reservation rejected.
All order-linked StockMovement writers guarded.
