# Pricing Registry UI audit — 2026-07-16

**Method:** Visual browser + read-only API cross-check  
**URL:** `http://127.0.0.1:3000/inventory/pricing`  
**Stack:** frontend `:3000`, backend `:8001` (LIVE / DB)  
**Writes:** none (no registry edits, no code changes)

## UI surface (exact)

| Item | Observed |
|------|----------|
| Page title | Pricing Registry |
| Data source badge | LIVE / DB — Sursa de date: backend live |
| Base currency note | Monedă de bază (Settings): EUR |
| Tabs | Acoperire template · Toate intrările · Verificare 5 · Adaos comercial · Istoric / audit |
| Default template scope | `TPL-VOLUMETRIC-LETTERS_v2` — Litere volumetrice (Product 001) |
| Template coverage stats | 37 confirmate · 2 review · 4 lipsă |
| Template picker options | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`, `TPL-METAL-PREMOUNT-STRUCTURE_v1`, `TPL-VOLUMETRIC-LETTERS_v2` only |
| Logo template in picker | **Absent** — search `logo` → “Niciun template găsit.” (`TPL-VOLUMETRIC-LOGO_v1` not listed) |

### Sections under Acoperire template (letters)

- Materiale → Plăci · Role / materiale flexibile · Profile / canturi · LED / electrice · Consumabile
- Servicii / operații → Alte operații · CNC / router / laser · Formare cant · Lipire cant · Vopsire / QC / ambalare

## Search log (exact term → visible result)

| Tab | Search term | Visible result |
|-----|-------------|----------------|
| Acoperire template | `print` | MAT-VINYL-PRINT 1,50 EUR/mp; MAT-VINYL-PRINT-LAMINATED 10,00 EUR/mp; LAMINATION 5,00 EUR/mp; LARGE_FORMAT_PRINT 8,50 EUR/mp — all Owner-confirmed |
| Acoperire / Toate | `VOL_V2_LOGO_PRINT_M2` | Niciun rând |
| Toate intrările | `logo` | Niciun rând |
| Toate intrările | `lamin` | MAT-VINYL-PRINT-LAMINATED 10 EUR/mp; SVC-LAMINATION-SERVICE Lipsă buc; LAMINATION 5 EUR/mp Owner-confirmed |
| Toate intrările | `aplic` | FACE_VINYL_APPLICATION_LABOR 5 EUR/mp; RETURN_CANT_VINYL_APPLICATION_LABOR 1 EUR/ml |
| Toate intrările | `montaj` | MAT-CONSUMABILE-MONTAJ 5 EUR/set Needs review; MAT-SABLON-MONTAJ 6 EUR/mp; LED_ASSEMBLY 0,05 EUR/buc — **no site-install row** |
| Toate intrările | `șablon` | MAT-SABLON-HARTIE 5 EUR/mp; MAT-SABLON-MONTAJ 6 EUR/mp |
| Toate intrările | `LARGE_FORMAT_PRINT` | Serviciu print autocolant 8,50 EUR / EUR/mp Owner-confirmed · TPL-VOLUMETRIC-LETTERS_v2 |
| Toate intrările | `santier` | Niciun rând |
| Toate intrările | `surub` | MAT-SURUBURI-GEN 5 EUR/set · TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 |
| Template picker | `logo` | Niciun template găsit |

Detail panel (LARGE_FORMAT_PRINT): kind = Rată operație / workcenter · Operații / Rate; value 8,50 EUR; unit EUR/mp; Owner-confirmed; impact În calcul ofertă; binding TPL-VOLUMETRIC-LETTERS_v2; min/setup not shown (null in API).

## Relevant registry entries (UI + API agree)

| Displayed name | Key/code | Classification | Status | Currency | Unit | Value | Min | Setup | Template binding | CPP finds it? |
|----------------|----------|----------------|--------|----------|------|-------|-----|-------|------------------|---------------|
| Serviciu print autocolant | `LARGE_FORMAT_PRINT` | operation_rate | active / Owner-confirmed | EUR | EUR/mp | 8.50 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | **No** (CPP key `VOL_V2_LOGO_PRINT_M2`, `documented_unit_price=null`) |
| Serviciu laminare print | `LAMINATION` | operation_rate | active / Owner-confirmed | EUR | EUR/mp | 5.00 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | **No** (`VOL_V2_LOGO_LAMINATE_M2`) |
| Manoperă aplicare folie fețe litere | `FACE_VINYL_APPLICATION_LABOR` | operation_rate | active / Owner-confirmed | EUR | EUR/mp | 5.00 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | **No** (`VOL_V2_LOGO_APPLICATION_M2`) |
| Folie print față litere | `MAT-VINYL-PRINT` | material | active / Owner-confirmed | EUR | mp | 1.50 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | No (material purchase, not CPP commercial service key) |
| Folie print + laminare | `MAT-VINYL-PRINT-LAMINATED` | material | active / Owner-confirmed | EUR | mp | 10.00 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | No (combined material SKU) |
| SVC-LAMINATION-SERVICE | `SVC-LAMINATION-SERVICE` | material stub | missing_price | — | buc | null | — | — | TPL-VOLUMETRIC-LETTERS_v2 | No (wrong unit + no price; do not use) |
| Șablon hârtie | `MAT-SABLON-HARTIE` | material | active / Owner-confirmed | EUR | mp | 5.00 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | Letters sablon uses DEV_BRIDGE commercial, not this material key directly in logo CPP |
| PVC 3 mm șablon montaj | `MAT-SABLON-MONTAJ` | material | active / Owner-confirmed | EUR | mp | 6.00 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | Same |
| Consumabile montaj | `MAT-CONSUMABILE-MONTAJ` | material | needs_review | EUR | set | 5.00 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | Not site-install commercial |
| Montaj module LED | `LED_ASSEMBLY` | operation_rate | active / Owner-confirmed | EUR | EUR/buc | 0.05 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | Not site-install |
| Suruburi / prinderi generale | `MAT-SURUBURI-GEN` | material | active / Owner-confirmed | EUR | set | 5.00 | none | none | TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 | ACM only; not volumetric site montaj |
| Ambalare litere volumetrice | `PACKAGING` | operation_rate | active / Owner-confirmed | EUR | EUR/mp | 10.00 | none | none | TPL-VOLUMETRIC-LETTERS_v2 | Packaging deferred (G5); CPP `ambalare` still pending binding |

Exact CPP commercial keys **not present** as registry codes: `VOL_V2_LOGO_PRINT_M2`, `VOL_V2_LOGO_LAMINATE_M2`, `VOL_V2_LOGO_APPLICATION_M2`, `VOL_V2_SITE_MOUNT_FUTURE`.

## UI vs API/code lookup

| Layer | Truth |
|-------|--------|
| UI `/inventory/pricing` | Owner-confirmed print / laminate / face-application rates exist under letters ops |
| API `GET /api/v1/pricing/registry` | Same 50 items; matches UI fields |
| CPP linked-logo rules | Fail-closed on `documented_unit_price=None`; **does not look up** `LARGE_FORMAT_PRINT` / `LAMINATION` / `FACE_VINYL_APPLICATION_LABOR` |
| Currency | Registry commercial ops = EUR; current logo body DEV_BRIDGE lines = RON — binding reuse needs FX/commercial currency policy, not a new invented rate |

## Conclusion per missing commercial line

| Missing CPP / owner code | Verdict | Reusable candidate (if any) |
|--------------------------|---------|-------------------------------|
| `logo_print` / `LOGO_PRINT_COMMERCIAL_RULE` / `VOL_V2_LOGO_PRINT_M2` | **EXISTING_TARIFF_BINDING_DEFECT** | `LARGE_FORMAT_PRINT` 8.50 EUR/mp (not `MAT-VINYL-PRINT` alone) |
| `logo_laminate` / `LOGO_LAMINATE_COMMERCIAL_RULE` / `VOL_V2_LOGO_LAMINATE_M2` | **EXISTING_TARIFF_BINDING_DEFECT** | `LAMINATION` 5.00 EUR/mp (ignore stub `SVC-LAMINATION-SERVICE` buc / missing) |
| `logo_application` / `LOGO_APPLICATION_COMMERCIAL_RULE` / `VOL_V2_LOGO_APPLICATION_M2` | **EXISTING_TARIFF_BINDING_DEFECT** | `FACE_VINYL_APPLICATION_LABOR` 5.00 EUR/mp |
| `montaj` / `MONTAJ_COMMERCIAL_RULE` / `VOL_V2_SITE_MOUNT_FUTURE` | **TRUE_OWNER_TARIFF_MISSING** | No site-install / șantier / locatie commercial rate in UI or registry |
| Installation template prep (material) | **EXISTING_TARIFF_REUSABLE** | `MAT-SABLON-HARTIE`, `MAT-SABLON-MONTAJ` |
| Mounting accessories | **EXISTING_TARIFF_BINDING_DEFECT** (scope mismatch) / not a logo CPP tariff gap | `MAT-CONSUMABILE-MONTAJ` (needs_review); `MAT-SURUBURI-GEN` ACM-only — neither is site-install labor |
| Stub `SVC-LAMINATION-SERVICE` | **EXISTING_TARIFF_WRONG_UNIT** (+ inactive/missing price) | Do not ask owner for this stub; use `LAMINATION` |

## T1–T6 eligibility (owner new-value pack)

Only **TRUE_OWNER_TARIFF_MISSING** may enter T1–T6:

1. **T1 — Site installation (montaj șantier)** commercial tariff (`VOL_V2_SITE_MOUNT_FUTURE` / `MONTAJ_COMMERCIAL_RULE`) — unit expected by CPP: `locatie` (fixed); no registry row exists.

**Removed from T1–T6 (do not ask owner for new numeric values):**

- Logo print → bind/reuse `LARGE_FORMAT_PRINT`
- Logo laminate → bind/reuse `LAMINATION`
- Logo application → bind/reuse `FACE_VINYL_APPLICATION_LABOR`

Owner may still be asked only for **reuse confirmation** (including EUR→commercial quote currency), not for inventing duplicate tariffs.
