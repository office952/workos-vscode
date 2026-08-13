# Lane G — classify only

| Artifact | Class | Evidence |
|----------|-------|----------|
| `/shop-floor` | ACTIVE / CANONICAL_MONITOR_HOME | Canonical production home; role home operator/manager |
| `/execution` | ACTIVE | Planificare; sales+manager+admin |
| `/execution/:id` | ACTIVE | Numeric order_id; Wave 2 order 973024 reachable |
| `/execution/machine-runs` | ACTIVE | Empty list this fixture; copy live |
| `/execution/ops-graph` | AUDIT_ONLY | Nav AUDIT; assign control exists, not used |
| `/execution/reality-review` | AUDIT_ONLY | Linked diagnostic |
| `/operator` | COMPAT_ACTIVE | Nav COMPAT; live `POST /operator/task-action`; FINITE_STATIC 75 277 px |
| `/tablet` | COMPAT_ACTIVE | Nav COMPAT; same operator API; `/tablet/print` drilled |
| `/employee-app-v2` | SPECIALIZED_EMPLOYEE_UI | Standalone; not in shell nav; observe only |
| Acțiune task / Stații | DUPLICATE_CANDIDATE | Two compat action UIs + mobile v2 |

No REMOVE_CANDIDATE_ONLY without consumer proof. Ugly ≠ dead.
