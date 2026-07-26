label: W7-T02 post-UTF8 re-verification
date: 2026-07-17
head: c9c1b67
backend: http://127.0.0.1:8001
frontend: http://127.0.0.1:3000
build1:
  order: 92402
  plan: 8
  quote_snapshot: QSN2-2026-0002
  total_amount: 3549.1286
  commercial_total: 3549.1286
  mojibake: false
scenarios:
  A_B:
    order: 92402
    summary: {matched: 1, missing_actual: 17, partial: 0, variance: 0, total: 18}
  C:
    order: 92403
    plan: 9
    summary: {matched: 0, missing_actual: 17, partial: 0, variance: 1, total: 18}
    variance: {planned_min: 0, actual_min: 75, delta: 75}
ui:
  - http://127.0.0.1:3000/execution/92402 Plan vs execuție
  - http://127.0.0.1:3000/execution/92403 Plan vs execuție varianță
modules: W7-T02 evidence visible under Surse și dovezi
tests:
  - pytest tests/test_post_job_truth.py -> 12 passed
  - vitest PostJobTruthPanel.test.tsx -> 4 passed
