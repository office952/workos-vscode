# Wave 5 — employee-record detail audit

| Field | Value |
|-------|--------|
| Route | `/employees-records/:employeeId` |
| Component | `frontend/src/pages/EmployeeProfile.tsx` |
| App.tsx | defined next to list (`/employees-records` + `/:employeeId`) |
| RBAC | `employees_records` → `view:hr` → manager / admin |
| Shell | `pathAllowedForRole` allows `/employees-records/*` for the same nav key |
| Runtime id | `7` (Andrei Goghi) |
| Mutations | 0 |

## Classification

```text
EMPLOYEE_RECORD_DETAIL_ROUTE = DEFINED_AND_REACHABLE
NAVIGATION_GAP = NO
NAVIGATION_AFFORDANCE = BUTTON_ONCLICK_NOT_ANCHOR
WAVE_5_INITIAL_SNR_CAUSE = RT_SELECTOR_A_HREF_MISS
```

Wave 5 initial RT searched `a[href*='/employees-records/']` and found **0**. That SNR is **SUPERSEDED** / **RESOLVED_BY_GAP_CLOSURE**. The list uses a full-width `<button onClick={() => navigate(\`/employees-records/${emp.id}\`)}>`. Lane H already listed that row as a GOOD_EDGE. Gap closure clicked the first of **8** row buttons and landed on `/employees-records/7`. Deep-link to the same URL also works.

Do **not** treat the missing `<a>` as a missing product affordance. Do **not** add a row link.

## Runtime

| Entry | Role | Theme | Result |
|-------|------|-------|--------|
| List row button | admin | light | REACHED `/employees-records/7` |
| Deep-link | admin | dark | REACHED |
| Deep-link | manager | light | REACHED |
| Deep-link | sales | light | redirected `/quotes` (MATCH) |
| Deep-link | operator | light | redirected `/shop-floor` (MATCH) |

Tabs opened (read-only): Profil · Documente · Medicina muncii · Alerte.

| Scroll | Value |
|--------|--------|
| SCROLL_CONTAINER | `main.overflow-auto` |
| SCROLL_START | 0 |
| SCROLL_END | 0 |
| SCROLL_MAX | 0 |
| BOTTOM_REACHED | YES |
| NEW_CONTENT_AFTER_FINAL_SCROLL | NO |
| SCROLL_SEGMENT_COUNT | 1 per tab |
| Nested | `workos-shell-nav` only (sidebar) |
| FULL_SCROLL_FAILURES | 0 |

The detail surface is finite and fits one viewport at 1440×900. Nested main overflow does not exist.

## Surface facts (observed)

- Identity: live name **Andrei Goghi**, role/department/skills from employee master.
- Badges: **DEMO** + **Confidențial**.
- Phone / email empty (mapper writes `""`).
- Program hardcoded: `Luni – Vineri` / `8h (+ 30 min pauză masă)`.
- Advance card: `Avans demonstrativ pe angajat live` / 300 lei.
- Documents: demo contract / fișă / medicina; `+ Adaugă document — coming soon` disabled; `Vezi fișier` disabled.
- No expandables beyond tabs. No write.

Shots: `wave-5/runtime/screenshots-gap-closure/` · log: `runtime/rt-gap-closure-log.json`.
