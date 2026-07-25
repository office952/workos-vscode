# Capac spate — structure documentation (canonical prose)

**Date:** 2026-07-23  
**Status:** locked display documentation (model = Vizual față)

Source: `frontend/src/features/product-system/lettersBackForexStructureDocumentation.ts`

## Role

Pasul 3 — Forex 10 mm · `MAT-SPATE-PVC-LITERE`. Debitare CNC obligatoriu; șanfren opțional (default fără).

## Cum calculăm

1. **Consum material:** `backing_area_m2` (fallback față→spate doar pentru mp)  
2. **Debitare CNC:** perimetru vectorial `back_cutting_perimeter_ml` × pass_count × tarif — nu bbox

Prețuri doar prin „Verifică…” spre Pricing Registry.
