# BUILD — Orders Execution UX Cleanup

**Status:** PASS (code + tests + read-only smoke)  
**Date:** 2026-06-12  
**Route:** `/orders/:orderId` — panou „Taskuri producție”

## 1. Problem UX

După fix-ul live-source guard (`e44c947`), flow-ul funcționa, dar Orders detail era confuz:

1. Textul panoului sugerea generare plan chiar când planul exista deja.
2. Două CTA-uri similare în același context:
   - „Vezi Execuția” (card traceability separat)
   - „Deschide execuția” (în panou)
3. NextStepPanel rămânea titluit „Generează taskuri producție” cu plan existent.

## 2. UX decision

| Stare | Panou | CTA principal |
|-------|-------|---------------|
| Live, fără plan | „Planul de execuție nu a fost generat” + explicație write-once | „Generează taskuri producție” |
| Live, cu plan | „Plan execuție existent” | **Un singur** „Vezi execuția” → `/execution/{orderDbId}` |
| Non-live | Warning existent | Fără panou / fără CTA |

Eliminat cardul traceability duplicat; CTA consolidat în `order-execution-dispatch-panel`.

## 3. Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/Orders.tsx` | Wording + CTA unic + NextStepPanel dinamic |
| `frontend/src/pages/Orders.executionCta.test.tsx` | Așteptări no-plan / cu-plan / fără duplicate |
| `frontend/src/pages/Orders.executionDispatch.test.tsx` | `order-view-execution-cta` după generate |
| `docs/qa/BUILD_ORDERS_EXECUTION_UX_CLEANUP.md` | Acest doc |

**Not touched:** `docs/mockups/` (untracked, ignored)

## 4. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/pages/Orders.executionCta.test.tsx `
  src/pages/Orders.executionDispatch.test.tsx `
  src/pages/Orders.empty.test.tsx
# 3 files, 9 passed
```

## 5. Runtime smoke (read-only)

**DB controlat:** order id `1`, code `ORD-1781201059-1`, 11 tasks existente.

| Check | Rezultat așteptat |
|-------|-------------------|
| `/orders/ORD-1781201059-1` | „Plan execuție existent”; text monitorizare (nu generare); **un** CTA „Vezi execuția” în panou; NextStep „Următorul pas: Vezi execuția” |
| Click CTA panou | Navigare `/execution/1` ✓ |
| `/execution/1` | **11** taskuri (11× Start); write-once blocker vizibil |

**Nu apăsat:** generate plan, start/assign/complete, convert.

## 6. Boundaries confirmed

- No DB changes
- No new orders / execution tasks
- No seed / migrations / schema
- No backend / Quotes / Operator / Tablet changes
- `docs/mockups/` not touched

## 7. Follow-ups (out of scope)

- Tablet flash demo pre-auth
- Unificare NextStepPanel vs panou (încă două zone, dar wording aliniat)
