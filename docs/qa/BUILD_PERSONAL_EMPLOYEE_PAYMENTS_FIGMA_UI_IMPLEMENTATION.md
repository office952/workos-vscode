# BUILD: Personal — Employee Payments Figma UI Implementation

## Purpose

Implement React UI for **Plăți angajați** per Figma design (tabs Tranșa 15 / Tranșa 30, scanable rows, recording modal). **No new backend** in this build.

## Figma reference

- File: [WorkOS — Plăți angajați](https://www.figma.com/design/eZfraKwGaBbNHHWUKxXKM9)
- Page: **Plăți angajați — Screens**
- Frames implemented in code:
  - 01 Desktop — Tranșa 15
  - 02 Desktop — Tranșa 30
  - 03 Modal — Înregistrează plată
  - 04–07 Card states (Neplătit / Parțial / Plătit / Warning)
  - 08 Detalii expandate

## Owner decision

Pagina este **informativă / operațională**:

- Afișează calculul din date existente (demo/local).
- Permite **înregistrarea sumei plătite efectiv** (state local).
- **Nu** configurează salarii, profile, pontaj, avansuri/datorii.
- **Nu** decide cât câștigă angajatul.

## What this page does NOT do

- No backend `employee_payment_records`
- No compensation profiles
- No schedule-preview API
- No salary/base editing on this screen
- No migrations or new routers/services

## UI behavior

### Tabs

- **Tranșa 15** — list shows only slot 15 per employee row.
- **Tranșa 30 / final lună** — list shows only slot 30.
- Never both tranșe on the same card.

### Filters / toolbar

- Chips: Toți, Neplătiți, Parțial, Plătiți (on active tab).
- Search angajat, sortare sumă rămasă / nume.

### Status logic (UI)

| Status   | Rule                                      |
|----------|-------------------------------------------|
| Neplătit | paid = 0 și remaining > 0                 |
| Parțial  | paid > 0 și remaining > 0                 |
| Plătit   | remaining ≤ 0                             |

Cancelled payments: istoric only; excluded from active paid totals.

### Master-detail layout decision

Spațiul din dreapta este folosit funcțional ca panou de lucru, nu ca zonă golă.

**Left panel (~60%)**

- Listă compactă angajați pentru tranșa activă (15 sau 30).
- Filtre, search, sortare.
- Rând: nume, pontaj/avansuri scurt, Calculat / Plătit / Rămas, status badge.
- Click selectează angajat; primul vizibil este selectat implicit.
- **Nu** există buton „Înregistrează plată” pe rânduri.

**Right panel (~40%, sticky desktop)**

- Detalii angajat selectat: header, summary tranșă, breakdown, pontaj, avansuri/datorii.
- Istoric plăți pentru angajat + lună + tranșă (anulate separate).
- Zona **Înregistrare plată**: Sumă rămasă readonly, Sumă plătită acum, dată, observații, Salvează plata.
- Dacă tranșa e plătită: „Tranșa este plătită”, formular disabled.

**Ce nu se modifică automat**

- Salariu / bază lunară.
- Pontaj.
- Avansuri/datorii (text: „Nu se închide automat din această pagină.”).

### Payment recording (right panel)

- Editable: Sumă plătită acum (default = rămas), Data plății, Observații.
- **Salvează plata** — partial payments supported (local/demo state).

### Warning

- Missing monthly amount: „Lipsește suma lunară în profilul angajatului.” + link „Deschide profil angajat”.

## Local / demo behavior

- `employeePaymentSituationDemo.ts` builds situations from demo calc + in-memory `recordedPayments` state.
- `usePersonalDemoModule` supplies employee registry (live names) + demo advances.
- **UI contract behavior** — not backend persistence. Marked in page comment.

## Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/EmployeePayments.tsx` | Master-detail: list + right detail/recording panel |
| `frontend/src/lib/employeePaymentSituationDemo.ts` | Slot detail breakdown for expanded rows |
| `frontend/src/pages/EmployeePayments.test.tsx` | Master-detail UI tests (11) |
| `frontend/src/pages/workforceRoutes.test.tsx` | Badge text update |

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeePayments.test.tsx src/pages/workforceRoutes.test.tsx
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeePayments.test.tsx
```

Result: **11 passed** (master-detail update).

## Boundary

- Frontend only.
- Backend unchanged (`e373deb` foundation: attendance + balances).
- **Page-scoped UI only** — no App shell, global CSS, or shared `ui` component changes. See `docs/architecture/WORKOS_UI_POLISH_STRATEGY.md`.

## Remaining for backend integration build

- Persist payment recordings API
- Read-only calculated amounts from profile + pontaj + balances (server-side)
- LIVE vs DEMO badge from real data source
- Cancel payment workflow tied to backend

## Next steps

1. Owner review `/employee-payments` against Figma frames.
2. Backend integration build (separate scope).
3. Optional: E2E smoke for payment recording flow.
