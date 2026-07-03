# Personal — Employee Payments Screen Contract

**Status:** Active — matches committed UI (`89c4023` master-detail rebuild)  
**Route:** `/employee-payments`

## 1. Purpose

The **Plăți angajați** page is an **informational and operational payment recording** surface for internal tranșa **15** and tranșa **30 / final lună**. Operators see what should be paid, what was already paid, and what remains — then record actual payments.

It is **not** payroll, **not** fiscal accounting, and **not** a configuration workspace for compensation.

## 2. Forbidden responsibilities

The page must **never**:

- Configure employee salary or monthly pay base
- Create or edit compensation profiles
- Edit employee profile fields (including salary/base) on this screen
- Edit attendance / pontaj
- Edit advances / debts ledger
- Decide or override how much an employee earns
- Auto-create payments from preview
- Auto-close debts or balances
- Use CostEngine or `cost_lunar_firma` as payment base
- Implement fiscal payroll, taxes, or legal gross/net salary

## 3. Allowed actions

- Select month (previous / current / next)
- Switch active tranșă tab: **Tranșa 15** or **Tranșa 30 / final lună**
- Filter list: Toți / Neplătiți / Parțial / Plătiți; search and sort employees
- View calculated payment situation per employee for the **active tranșă**
- View paid and remaining amounts per slot and aggregated month summary
- Select an employee (default: first visible in filtered list)
- **Record** how much was actually paid (full or partial) in the right panel
- Set payment date and notes on a recording
- View per-employee payment history for month + active tranșă; cancelled entries in history only

## 4. Data sources

| Data | Current (demo) | Future live mode | Payments page role |
|------|----------------|------------------|-------------------|
| Monthly pay base | Demo module / profile read | Employee profile (not CostEngine) | Read-only input to calculation |
| Attendance | Demo summary | Event-based pontaj | Read-only summary |
| Advances / debts | Demo advances | Employee balances (`e373deb`) | Read-only summary |
| Recorded payments | **In-memory React state** (`recordedPayments`) | Future payment ledger API | Create + list; no persistence today |

**Backend persistence of recordings is deferred** to a separate integration build.

## 5. Calculation concept

Calculation is **read-only display** on this page:

- Expected tranșa ≈ 50% of monthly internal base plus/minus period adjustments (attendance, overtime, retentions) — demo today; server-defined in future build
- **Paid** = sum of active (non-cancelled) recorded payments for that slot
- **Remaining** = expected − paid (≥ 0)
- **Monthly calculated** = expected slot 15 + expected slot 30 for the month

The page does not expose calculation knobs.

## 6. UI layout (master-detail)

After header, month selector, summary cards, tranșă tabs, and filters:

### Left panel (~55–65%)

- Compact list of employees for the **active tranșă only** (15 or 30 — never both on one row).
- Each row: name, short pontaj status, short advances/debts summary, Calculat / Plătit / Rămas, status badge (Neplătit / Parțial / Plătit).
- Click selects employee; selected row is visually highlighted.
- **No** per-row „Înregistrează plată” button.

### Right panel (~35–45%, sticky on desktop)

- Header: employee name, active tranșă label, status badge.
- Summary: Calculat / Plătit / Rămas for active tranșă.
- Breakdown: bază calculată, ajustare pontaj, ore suplimentare, avansuri/datorii, plăți existente, rămas.
- Pontaj: status + warning if incomplete.
- Avansuri/datorii: sold activ, reținere sugerată if applicable; text: „Nu se închide automat din această pagină.”
- Istoric plăți for employee + month + active tranșă (cancelled shown separately).
- **Înregistrare plată** (inline, not a modal): Sumă rămasă (readonly), Sumă plătită acum, Data plății, Observații, **Salvează plata**.

### Empty / edge states

- No employees in filter → empty list; right panel empty state.
- Missing pay base → warning in detail panel + link to open employee profile **outside** this page (no salary edit here).
- Tranșa fully paid → „Tranșa este plătită”; recording form disabled.

### Responsive

- Desktop/laptop: two columns when space allows.
- Small screens: detail may stack below list.

## 7. Payment recording behavior

- Recording happens in the **right panel** for the selected employee and **active tranșă tab**.
- Readonly: Sumă rămasă; editable: Sumă plătită acum (default = remaining), date, notes.
- Operator may pay less than remaining → partial payment.
- Saving updates paid / remaining / status immediately in UI (local state today).
- No automatic debt mutation, pontaj change, or salary change.

## 8. Partial payment behavior

- If paid &lt; expected for a slot → status **Parțial**, remaining &gt; 0
- Additional recordings can be added until remaining = 0 → **Plătit**
- Partial does not imply debt closure

## 9. Remaining amount behavior

- Remaining is per slot and aggregated for month summary cards
- Cancelled history entries are excluded from paid totals
- Switching tranșă tab updates list, detail, and form for the same selected employee when present in the new list

## 10. Future backend integration boundary

**Next build (separate scope):** persist recordings via minimal payment ledger API; expose read-only calculated expected amounts from profile + pontaj + balances.

**Still out of scope on this screen:** compensation-profile configuration, schedule-preview APIs, salary editing, migrations for rejected WIP directions.

**Rejected WIP reference (local archive only):** `C:\Users\offic\workos-local-backups\2026-06-11-employee-payments-rollback\ROLLBACK_SAFETY_EMPLOYEE_PAYMENTS_WIP.patch` — not in repo; do not reapply without explicit charter.

---

*Current implementation: demo/mock calculation + in-memory `recordedPayments` — see `docs/qa/BUILD_PERSONAL_EMPLOYEE_PAYMENTS_FIGMA_UI_IMPLEMENTATION.md`.*
