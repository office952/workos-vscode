# Canonical Finish Enum Map — Owner Decision v1

> **Notă:** Acest document este decizie owner pentru maparea finish pe suprafețe.  
> **Nu** este sursă runtime. **Nu** activează pricing. **Nu** scrie Product Truth live.  
> **Nu** autorizează FINISH workshop sau ProductDefinition bridge până la slice-urile permise de mai jos.

**Date:** 2026-07-09  
**HEAD la semnare:** `0a4a346` — Deduplicate RETURN-CANT RAL pricing keys  
**Owner:** Alex / P-Media

---

## Context

Deciziile din acest document se bazează pe auditurile:

- `FINISH_vs_RETURN_CANT_BOUNDARY_DECISION_AUDIT_PLAN_V1`
- `CANONICAL_FINISH_ENUM_UNIFICATION_MAP_V1`
- `CANONICAL_FINISH_ENUM_MAP_OWNER_DECISION_APPLY_DOC_V1`

Concluzii de context:

1. WorkOS finish semantics sunt **separate pe suprafață** în Intake V6: **cant**, **face**, **artwork**.
2. Product System trebuie să mapeze finish prin **`surface_target` + `technical_variant`**, nu printr-un finish global/generic.
3. Căile generice FINISH (`product.components.finish.oracal_code`, `ral_code`, `stock_color`) sunt **retrase conceptual** — nu se implementează în workshop FINISH sau bridge runtime.
4. RETURN-CANT rămâne owner pentru finisajul aplicat pe cant/return/side; FINISH preia doar tratamentul vizual pe față și artwork.

---

## Owner decision table

| Decision | Owner answer | Status | Notes |
|----------|--------------|--------|-------|
| **A. Face vinyl ownership** | **ACCEPT** | `owner_confirmed` | FINISH deține aplicația vinyl pe față (`product.components.finish.face.vinyl.*`). FACE deține doar substrat/geometrie: material, grosime, cut path, referințe area/perimeter. |
| **B. Artwork / Vector Logo finish ownership** | **ACCEPT** | `owner_confirmed` | FINISH deține finisaj artwork sub `product.components.finish.artwork.instances[]` pentru acum. Componentă Logo viitoare poate reutiliza/migra cu owner GO explicit. |
| **C. Truth path split** | **ACCEPT** | `owner_confirmed` | Se acceptă `product.components.finish.face.*` și `product.components.finish.artwork.*`. Se resping generic `product.components.finish.oracal_code` / `ral_code` / `stock_color`. |
| **D. Cant exclusion** | **ACCEPT** | `owner_confirmed` | Cant stock / Oracal / RAL sunt **excluse permanent** din FINISH. Rămân doar sub `product.components.return_cant.*` incl. `finish.variant`, coduri, referințe pricing keys, politica RAL minimum. |
| **E. Print + laminare ownership** | **ACCEPT** | `owner_confirmed` | Print + laminare este **FINISH-only** pe face și artwork. RETURN-CANT **nu** deține niciodată print/laminate. |

---

## Canonical ownership summary

### RETURN-CANT owns

- `cant_stock_color`
- `cant_oracal_wrap`
- `cant_ral_paint`
- `cant_ral_minimum_policy` (100 lei · owner commercial policy · **not** Pricing Registry)
- Truth paths under `product.components.return_cant.*`
- Pricing key references: `/inventory/pricing` (readonly cross-ref in Product System workshop)
- Catalog cross-ref: Intake V6 Color Registry (readonly — no duplication in Product System)

### FINISH owns

- Face vinyl (`face_oracal_641`, `face_oracal_651`, `face_oracal_8500`)
- Face print + laminare (`face_print_laminate`)
- Artwork vinyl / print / laminate (`artwork_print_laminate`, `artwork_print_only`, `artwork_cut_vinyl`, `artwork_translucent_vinyl`)
- Truth paths under `product.components.finish.face.*`
- Truth paths under `product.components.finish.artwork.instances[]`
- Pricing: shared MAT keys allowed where applicable; labor e.g. `FACE_VINYL_APPLICATION_LABOR` on face — **not** cant labor keys

### FACE owns

- Substrate
- Material
- Thickness
- Cut path / geometry
- Face area / perimeter refs (basis for FINISH quantity, not finish application ownership)

---

## Retired conceptual paths

Aceste căi **nu se implementează** în workshop FINISH sau bridge runtime. Pot apărea încă în contracte readonly vechi până la slice de aliniere cod — status: **deprecated_conceptual**.

| Retired path | Reason | Replacement |
|--------------|--------|-------------|
| `product.components.finish.oracal_code` | Generic; duplică Oracal cant; fără `surface_target` | Face: `product.components.finish.face.vinyl.*` · Artwork: `product.components.finish.artwork.instances[].vinyl.*` · Cant: `product.components.return_cant.finish.vinyl.*` |
| `product.components.finish.ral_code` | Generic; duplică RAL cant | Cant: `product.components.return_cant.finish.paint.ral_code` · Face paint (dacă va exista): `product.components.finish.face.paint.*` — decizie separată viitoare |
| `product.components.finish.stock_color` | Generic; duplică stock cant | Cant: `product.components.return_cant.finish.stock_color_label` · Face raw: FACE substrat + FINISH `face.variant=none` |
| `product.components.finish.type` | Ambiguu fără suprafață | `return_cant.finish.variant` · `finish.face.variant` · `finish.artwork.instances[].variant` |

**Harmonizare viitoare (contract doc, nu runtime):** workshop `return_cant.finish_type` ↔ mapping `return_cant.finish` → canonical `return_cant.finish.variant`.

---

## Still forbidden (after this doc)

- FINISH workshop implementation
- ProductDefinition bridge implementation
- Product Truth live write
- Pricing activation from Product System contracts
- Work Intake exposure for component-first set
- Catalog duplication in Product System (Oracal/RAL lists)
- Generic FINISH fields: `finish.oracal_code`, `finish.ral_code`, `finish.stock_color`
- Cant pricing keys in FINISH: `MAT-VOPSEA-RAL-CANT-*`, `RETURN_CANT_RAL_PAINT_LABOR`, `RETURN_CANT_VINYL_APPLICATION_LABOR` (în context FINISH)
- 100 lei RAL minimum în Pricing Registry
- Legacy delete (`TPL-VOLUMETRIC-FINISH_v1` rămâne evidence până la replacement readiness)

---

## Next allowed slices (after this doc)

| Order | Slice | Type |
|-------|-------|------|
| 1 | `CANONICAL_FINISH_ENUM_MAP_READONLY_CONTRACT_V1` | Readonly architecture doc + optional readonly TS contract |
| 2 | `FACE_COMPONENT_TRUTH_WORKSHOP_V1` | Product System readonly workshop — substrat/geometrie |
| 3 | `FINISH_COMPONENT_WORKSHOP_V1` | Doar după boundary FACE clarificat; paths `finish.face.*` / `finish.artwork.*` only |
| 4 | ProductDefinition bridge mapping | După contract enum + FACE/FINISH workshops stabile |

**Fără activare runtime** în niciun slice de mai sus fără build owner GO dedicat.

---

## Owner sign block

```
Owner: Alex / P-Media
Date: 2026-07-09

A. Face vinyl ownership          -> ACCEPT
B. Artwork / Vector Logo finish  -> ACCEPT
C. Truth path split              -> ACCEPT
D. Cant exclusion                -> ACCEPT
E. Print + laminare ownership    -> ACCEPT
```

---

## Delivery reference

| Field | Value |
|-------|-------|
| Task | `CANONICAL_FINISH_ENUM_MAP_OWNER_DECISION_DOC_WRITE_V1` |
| Mode | DOC WRITE ONLY |
| Forbidden scope | No runtime, no FINISH workshop, no bridge, no pricing activation |
