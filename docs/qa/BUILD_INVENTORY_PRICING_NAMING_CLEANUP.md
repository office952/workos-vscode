# BUILD — Inventory / Pricing Naming Cleanup (non-breaking)

**Date:** 2026-06-09  
**Type:** Seed display names + source_notes + hint tuning + catalog docs  
**DB schema:** Not touched  
**CostEngine:** Not touched  
**material_code rename:** Not done

---

## Scope

Controlled cleanup of material **display names** and **source_notes** in seeds and owner-confirmed price patches, aligned with `MATERIAL_CANONICAL_NAMING_AND_ALIASES.md`.

**Not in scope:** code rename, material deletion, DB migration, CostEngine formulas, TPL-STRUCTURA-LITERE.

---

## Implemented

| Area | Change |
|------|--------|
| **Central catalog** | `backend/seeds/material_canonical_naming.py` — canonical `name` + `source_notes` per high-risk code |
| **Seeds** | `seed_build4_materials`, `seed_inventory_materials_stubs`, `seed_acm_bond_materials` apply catalog on insert |
| **Owner patches** | `seed_volumetric_owner_confirmed_prices`, `seed_acm_owner_confirmed_prices` canonical names on patch |
| **Frontend catalog** | `materialRegistryNamingCatalog.ts` — documented code → canonical name |
| **UI hints** | Suppress alias/brand noise when name is already substantially canonical; usage warnings remain |
| **Tests** | `test_material_canonical_naming.py`, extended vitest suites |

---

## UI hints review (logic / vitest smoke)

| Input | Expected | Blocking save? |
|-------|----------|----------------|
| `bond 3mm` | Alias → Panou compozit aluminiu | No |
| `dibond alb 3mm` | Alias + brand hint | No |
| `forex 10mm` | PVC expandat family | No |
| `stiplex 3mm` | PMMA family | No |
| `oracal 651 galben` | Folie + brand + serie | No |
| `bare premontaj otel 30x30x1.5` | Oțel + **usage warning** | No |
| `profil aluminiu caseta` | Profil aluminiu + usage warning | No |
| `PVC expandat 10 mm` | **No alias noise** (canonical) | No |

Hints do **not** auto-edit input.

---

## Materials updated (display name / notes — codes unchanged)

| Code | Canonical name (target) | Notes |
|------|-------------------------|-------|
| MAT-PREMOUNT-BAR-STEEL | Țeavă pătrată oțel 30×30×1.5 mm | premount = usage in notes |
| MAT-PREMOUNT-BAR-ALUMINUM | Țeavă pătrată aluminiu 30×30×1.5 mm | idem |
| MAT-SPATE-PVC-LITERE | PVC expandat 10 mm | Forex = alias in notes |
| MAT-SABLON-MONTAJ | PVC expandat 3 mm — șablon montaj | usage in notes |
| MAT-ACM-BOND-* | Panou compozit aluminiu (ACM/ACP) N mm | Dibond/bond in notes |
| MAT-ACP-3MM | Panou compozit aluminiu (ACM/ACP) 3 mm | dedup warning vs MAT-ACM-BOND-3MM |
| MAT-ACP-FATA-LITERE | PMMA / plexiglas acrilic 3 mm — față litere | ACP code legacy |
| MAT-ORACAL-651 | Folie autocolantă PVC — Oracal 651 | brand/serie |
| MAT-PLEXI-* | PMMA / plexiglas acrilic … | Plexiglas alias in notes |

---

## Remaining risks (future migration)

- `MAT-ACP-3MM` vs `MAT-ACM-BOND-3MM` duplicate rows (same family)
- `MAT_ORACAL_*` vs `MAT-ORACAL-*` namespace split (Product 001)
- `MAT-PREMOUNT-BAR-*` codes contain usage — target `MAT-STEEL-SQUARE-TUBE-*` needs alias resolver
- ACM foil thickness not in generic 3 mm SKU names yet
- Existing DB rows unchanged until re-seed / owner patch re-run

---

## Tests

```bash
cd frontend
npx vitest run src/lib/materials/
npx tsc -b --noEmit

cd ../backend
python -m pytest tests/test_material_canonical_naming.py tests/test_volumetric_owner_confirmed_prices.py -q
```

---

## Follow-up

1. Owner UI review of Material Price Registry hints in production-like data
2. DB patch script to refresh `name`/`source_notes` on existing rows (optional)
3. Code alias migration for premount bars + ACM deduplication

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-09 | Initial non-breaking naming cleanup build |
