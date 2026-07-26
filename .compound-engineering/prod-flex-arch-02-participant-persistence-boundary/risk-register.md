# PROD-FLEX-ARCH-02 — Risk Register

Distinct risks for persistence boundary decision — not duplicated in decision-log defaults.

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R-ARCH-01 | Removing `_has_active_session_by_other` before split pools | **High** | FLEX-03 must ship helper pool before guard change |
| R-ARCH-02 | `assigned_employee_id` conflated with participant list | **High** | HELPER-only membership; principal stays `assigned_employee_id` only (OWNER-DECISION-08 P7) |
| R-ARCH-11 | Persisted PRINCIPAL membership duplicates assignee | **High** | **Rejected** — no PRINCIPAL row at FLEX-02 |
| R-ARCH-12 | JOIN interpreted as session start or claim | **High** | JOIN = membership only per P8 |
| R-ARCH-13 | LEAVE stops other workers' sessions | **High** | LEAVE = own membership only per P9 |
| R-ARCH-14 | Architecture sign-off read as FLEX-02 auto-GO | **High** | P11=NO explicit; gate outcomes corrected |
| R-ARCH-03 | `participants_json` reintroduced as shortcut | **High** | Owner rejected; enforce normalized tables only |
| R-ARCH-04 | Dual-write drift (membership vs sessions) | **Medium** | Sessions = work proof only; membership = authorization to work |
| R-ARCH-05 | Rematerialize operational tasks orphaning sessions | **High** | Never rematerialize orders with session history without identity map |
| R-ARCH-06 | TaskClarificationRequest reused as help | **Medium** | Separate `execution_task_help_requests` entity |
| R-ARCH-07 | Premature FLEX-02 without separate owner GO | **High** | P11=NO; OWNER-DECISION-08 complete; FLEX-02 blocked until explicit kickoff |
| R-ARCH-08 | Event log as sole authority | **Medium** | Events supplement only; membership rows authoritative for queries |
| R-ARCH-09 | Legacy orders (T-001 IDs) vs V2 graph keys | **Medium** | Scope persistence to V2 materialized path first; legacy adapter |
| R-ARCH-10 | Multiple execution_plan rows per order | **Low** | Anchor on `(order_id, task_id)`; record `execution_plan_id` provenance |
