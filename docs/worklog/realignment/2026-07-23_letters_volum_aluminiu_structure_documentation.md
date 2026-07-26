# Volum aluminiu — structure documentation (canonical prose)

**Date:** 2026-07-23  
**Status:** locked display documentation (model = Vizual față)

Source of truth for UI prose: `frontend/src/features/product-system/lettersVolumeAluminumStructureDocumentation.ts`

## Role

Pasul 2 — cant / lateral din profil aluminiu Al 0.6 mm. Consumă `face_perimeter_length_m`; nu inventează perimetru.

## Material

- Familie: Volum aluminiu · profil Al 0.6 mm
- Selector: `MAT-PROFIL-LATERAL-LITERE` → lățime după `return_depth_mm`
- SKU: `MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM`
- Nu: ACM / premontaj / casetă

## Cum calculăm

1. **Consum profil:** `quantity_ml = face_perimeter_length_m` · cost = ml × registry €/ml pe SKU lățime  
2. **Finisaj cant:** stock fără extra; Oracal pe mp (rolă × lungime); RAL pe ml + labor

Prețurile nu se dublează în Lab UI — doar „Verifică…” spre Pricing Registry.
