# BUILD — Quote Component Breakdown Real Source Fix

**Status:** PASS (code + unit tests + read-only smoke)  
**Date:** 2026-06-12  
**Route:** `/quotes/:quoteId` — secțiunea „Breakdown pe componente”

## 1. Problem

Quote detail afișa **13 rânduri identice** (`layer_1…layer_13`, tip `structure`, costuri împărțite uniform), deși:

- Backend persistă deja `component_breakdown` real (CostEngine v2) în `quotes.line_items` Shape B
- TPL-VOLUMETRIC-LETTERS produce ~6 componente business (`comp_face_litere`, …)
- Totalul aggregate al quote-ului era corect; doar breakdown-ul per componentă era **misleading**

## 2. Root cause

În `frontend/src/lib/dataStore.ts`, funcția `extractQuotePayload` (Shape B) apela:

```ts
deriveBreakdownFromCanonical(parsed.line_items) ?? parsed.component_breakdown
```

`deriveBreakdownFromCanonical` împarte `cost_result.materials_cost` / `labour_cost` uniform pe `product_definition.layers` (13 layere sintetice din `required_materials_json`). Această derivare **câștiga mereu** când snapshot-ul canonic avea layers — ignorând `component_breakdown` persistat.

## 3. Fix applied

### `frontend/src/lib/dataStore.ts`

1. **`resolveComponentBreakdown(persisted, snapshot)`** — prioritate:
   - `normalizeComponentBreakdown(parsed.component_breakdown)` dacă array ne-gol
   - altfel `deriveBreakdownFromCanonical(snapshot)` (legacy fallback)

2. **`normalizeComponentBreakdown`** — mapper defensiv minim (fără inventare costuri):
   - `component_name` → `name`, `component_type` → `type`
   - `materials` / `operations` → `materials_detail` / `operations_detail`
   - costuri doar când prezente în payload

3. **`extractQuotePayload`** exportată pentru teste; Shape B folosește `resolveComponentBreakdown`.

## 4. Legacy fallback (păstrat)

Quotes vechi **fără** `component_breakdown` în wrapper continuă să afișeze derivarea sintetică pe layers (comportament pre-fix). Marcat în teste ca „legacy synthetic layer split”.

Shape C (snapshot canonic top-level, fără wrapper) — același fallback sintetic; nu există câmp `component_breakdown` la acel nivel.

## 5. Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/dataStore.ts` | Precedence fix + normalizare defensivă + export `extractQuotePayload` |
| `frontend/src/lib/dataStore.extractQuotePayload.test.ts` | Teste Shape B/C, real vs synthetic, normalizare câmpuri |
| `docs/qa/BUILD_QUOTE_COMPONENT_BREAKDOWN_REAL_SOURCE_FIX.md` | Acest doc |

## 6. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/dataStore.extractQuotePayload.test.ts `
  src/lib/dataStore.test.ts
# 2 files, 10 passed
```

## 7. Runtime smoke (read-only)

**Fixture:** `QT-E2E-COMMERCIAL-001` (dev.db)

- `component_breakdown`: 6 componente (`comp_face_litere`, …)
- `product_definition.layers`: 13 (proxy materiale — nu afișate după fix)

**Verificări (2026-06-12, stack :3000/:8000 live):**

| Check | Înainte | După (observat) |
|-------|---------|-----------------|
| Număr rânduri breakdown | 13 identice | **6** componente business |
| ID-uri | `layer_1…layer_13` | **`comp_face_litere` … `comp_premount_bars`** |
| Costuri per rând | uniforme (~51,19) | **diferențiate** (ex. 118,15 / 270,05 / 127,13) |
| Total quote aggregate | neschimbat | **1.104,33 RON** (928,01 EUR fără TVA) |
| Convert enabled | da (post 30b0918) | **„Creează comandă din oferta activă” enabled** |
| Document comercial | coerent | Previzualizare + Descarcă HTML prezente |

**Nu s-a apăsat convert.** Fără seed / fără modificări DB.

## 8. Boundaries confirmed

- No backend changes
- No CostEngine / pricing / ProductSystemService changes
- No DB / seed / migrations / schema changes
- No Orders / Execution / Employee Payments / Operator / Tablet changes
- Breakdown **nu** ascuns — afișează sursa reală când există

## 9. Follow-ups (out of scope)

- Eliminare completă fallback sintetic când nu mai există quotes legacy fără `component_breakdown`
- Aliniere `product_definition.layers` la componente ierarhice (backend, build separat)
