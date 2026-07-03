# BUILD — Personal Employee Payments Rebuild (Rollback Chronicle)

**Type:** Historical QA evidence — rollback context only  
**Superseded UI implementation:** `docs/qa/BUILD_PERSONAL_EMPLOYEE_PAYMENTS_FIGMA_UI_IMPLEMENTATION.md` (committed `89c4023`)  
**Screen contract:** `docs/architecture/PERSONAL_EMPLOYEE_PAYMENTS_SCREEN_CONTRACT.md`

> The card-layout + modal UI described in early rebuild notes was replaced by **master-detail** (left list + right detail/recording panel). Do not use this file for current UI behavior.

## Purpose of this document

Preserve **why** the Payments page was rebuilt and **what was rejected**, after rollback from an over-scoped WIP. Operational UI details live in the Figma BUILD doc and screen contract.

## Rollback context

- Employee Payments WIP (schedule-preview, compensation profiles, `employee_payment_records` backend) was rolled back to `e373deb`.
- **Rejected direction:** schedule-preview-first UI with salary/base configuration on the Payments page.
- **Owner correction:** page is informational + payment recording only — no salary/profile/pontaj/debt editing.

## Local archive (not in repo)

Artifacts moved to:

`C:\Users\offic\workos-local-backups\2026-06-11-employee-payments-rollback\`

| File | Role |
|------|------|
| `ROLLBACK_SAFETY_EMPLOYEE_PAYMENTS_WIP.patch` | Full WIP capture — **not reapplied** |
| `ROLLBACK_SAFETY_GLOBAL_UI_UX_CLEANUP.patch` | Global shell/CSS WIP — see `docs/architecture/WORKOS_UI_POLISH_STRATEGY.md` |
| `dev.db.bak-*` | Pre-migration SQLite snapshots |

Patches are **local reference only**. Do not apply without explicit charter and impact audit.

## What shipped instead (committed)

- `89c4023` — `feat(personal): rebuild employee payments UI` (master-detail, tabs 15/30, inline recording, demo state)
- `a53292c` — `docs(ui): add WorkOS UI polish strategy`

## Backend

No payment persistence API in the rebuild path. Balances/attendance foundations remain at `e373deb` lineage; ledger integration deferred.

## Next build (unchanged)

1. Persist recordings via minimal payment ledger API
2. Read-only calculated amounts from profile + pontaj + balances (server-side)
3. Still no salary/profile editing on this page
