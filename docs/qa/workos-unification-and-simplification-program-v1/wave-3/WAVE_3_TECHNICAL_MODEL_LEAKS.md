# Wave 3 — TECHNICAL_MODEL_LEAK_TO_UI

| # | route | element | internal truth | user need | severity | disposition |
|---|-------|---------|----------------|-----------|----------|-------------|
| 1 | `/shop-floor` | `CNC_ROUTING` / `LETTER_FORMING` | WC enum | station name | HIGH | RENAME |
| 2 | `/shop-floor` | next-step → COMPAT | architecture split monitor/action | do the job | HIGH | SIMPLIFY |
| 3 | `/execution/:id` | URL `973024` | DB order_id | order code | HIGH | MERGE identity |
| 4 | `/operator` | policy string | gate enum | can I start? | HIGH | HIDE |
| 5 | `/operator` | `assigned - Neatribuit` | two status models | one state | HIGH | MERGE |
| 6 | `/operator` | JOB-23099 | job key | which piece | MED | disclosure |
| 7 | nav | AUDIT/COMPAT chips | program status | work | MED | HIDE_BY_ROLE |
| 8 | `/execution` | numeric rows | observability ids | which order | MED | show code |
| 9 | FLUX | Control producție in operator path | admin home | next job | MED | MOVE |
| 10 | ops-graph | fixture/order form | QA fixture | audit only | LOW | AUDIT_ONLY |
| 11 | employee-app-v2 | unlinked parallel | mobile stack | find my task | MED | MOVE/link later |
| 12 | Print card | util% / Runtime 0min | telemetry | is it printing? | LOW | MANAGER |

Count = **12**
