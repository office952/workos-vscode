# PROD-FLEX-ARCH-02 — Risk Register

Distinct risks for persistence boundary decision — not duplicated in decision-log defaults.

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R-ARCH-01 | Removing `_has_active_session_by_other` before split pools | **High** | FLEX-03 must ship helper pool before guard change |
| R-ARCH-02 | `assigned_employee_id` conflated with participant list | **High** | Keep principal as hint; membership table for HELPER/PRINCIPAL roles |
| R-ARCH-03 | `participants_json` reintroduced as shortcut | **High** | Owner rejected; enforce normalized tables only |
| R-ARCH-04 | Dual-write drift (membership vs sessions) | **Medium** | Sessions = work proof only; membership = authorization to work |
| R-ARCH-05 | Rematerialize operational tasks orphaning sessions | **High** | Never rematerialize orders with session history without identity map |
| R-ARCH-06 | TaskClarificationRequest reused as help | **Medium** | Separate `execution_task_help_requests` entity |
| R-ARCH-07 | Premature FLEX-02 without owner P4 sign-off | **High** | P11 remains NO until decision-log signed |
| R-ARCH-08 | Event log as sole authority | **Medium** | Events supplement only; membership rows authoritative for queries |
| R-ARCH-09 | Legacy orders (T-001 IDs) vs V2 graph keys | **Medium** | Scope persistence to V2 materialized path first; legacy adapter |
| R-ARCH-10 | Multiple execution_plan rows per order | **Low** | Anchor on `(order_id, task_id)`; record `execution_plan_id` provenance |
