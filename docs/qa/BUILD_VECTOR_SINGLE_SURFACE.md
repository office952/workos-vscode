# BUILD-VECTOR-SINGLE-SURFACE

## Pre-flight

| Item | Value |
|------|-------|
| Branch | `master` |
| HEAD (before) | `9b63934` |
| Working tree | clean (before implementation) |
| Backend :8000 | 200 OK |
| Frontend :3000 | 200 OK |

### Counts

| | Before | After |
|---|--------|-------|
| intakes | 22 | 22 |
| quotes | 7 | 7 |
| orders | 8 | 8 |

No intakes modified during smoke.

---

## Duplicate vector surface audit (Phase 1)

| vector data / action | Fast Ask (before) | Vector Studio §9 (before) | duplicate? | source of truth (before) | recommended owner |
|----------------------|-------------------|---------------------------|------------|------------------------|-------------------|
| file name | file pick + text input | duplicate text input | yes | both wrote `vector_file_name` | **Vector Intake & Review** |
| file present | via pick | implied | partial | Fast Ask pick | **Vector Intake & Review** |
| file quality notes | text input | — | no | Fast Ask | **Vector Intake & Review** |
| file MIME/size | pick metadata | — | no | Fast Ask | **Vector Intake & Review** |
| SVG dimensions/viewBox | client analysis | server paste analysis | yes | both | **Vector Intake & Review** (client); server paste retired for vector pathway |
| detected layer count | client `analyzeSvgVectorFile` | server `analyzeLayers` | yes | both | **Vector Intake & Review** |
| detected layer names | layer rows | live + persisted rows | yes | both | **Vector Intake & Review** |
| suggested roles | `VECTOR_LAYER_ROLE_OPTIONS` | `MANUAL_SVG_LAYER_MAPPING_TARGETS` | yes | both | **Vector Intake & Review** |
| confirmed roles | role selectors | mapping targets | yes | both | **Vector Intake & Review** |
| layer alignment | dropdown | partial via spec | partial | Fast Ask | **Vector Intake & Review** |
| manual review required | — | checkbox | no (missing above) | §9 only | **Vector Intake & Review** |
| review notes | layer notes on apply | textarea | yes | §9 live; Fast Ask on apply | **Vector Intake & Review** |
| apply/prefill action | CTA | — | no | Fast Ask | **Vector Intake & Review** |
| warnings | parse warnings | InfoCards + warnings | yes | both | **Vector Intake & Review** (read-only summary) |
| status / confirmed mapping | partial | full InfoCards | yes | §9 persisted | **Vector Intake & Review** (badges + saved mappings list) |

---

## Code ownership audit (Phase 2)

| field/action | owner today | desired owner | migration needed? | risk |
|--------------|-------------|---------------|-------------------|------|
| file selection | `VectorIntakeFastAskPanel` | same (renamed surface) | no | low |
| detected layers display | Fast Ask + `VectorStudioPanel` | Fast Ask only (vector pathway) | hide §9 | low |
| role confirmation | Fast Ask + Vector Studio | Fast Ask only | hide §9 | low |
| layer alignment | Fast Ask | Fast Ask | no | low |
| review notes | Vector Studio (+ apply merge) | unified surface | wire `onManualReviewChange` | low |
| apply to spec | `mapVectorFastAskToProductSpec` | unchanged | no | low |
| persistence | `Product001IntakeSpecEditor` | unchanged | no | low |
| manual review checkbox | Vector Studio §9 | unified surface | move UI only | low |
| SVG paste / server analyze | Vector Studio §9 | hidden on vector pathway | visibility only | medium — manual pathway never showed §9 |
| saved mapping summary | Vector Studio InfoCards | review section badges | read-only display | low |
| geometry sections 1–8 | `Product001IntakeSpecEditor` | unchanged | no | low |

Fields only in Vector Studio (preserved in `product_spec_json`, not deleted):

- `vector_parse_status`, `vector_analysis_status`, `vector_detected_layers_summary`
- `svg_layer_mappings` (server-side mapping targets)
- `vector_preview_available`, analysis warnings

Fields only in Fast Ask (remain visible):

- production quick questions (face colantare, cant, depth, lighting)
- client-side layer role confirmation
- file pick metadata

---

## Single-surface decision (Phase 3)

**Option 1 — adopted**

For `pathway === "vector"`:

- Show one **Fișier vector și layere** surface (`VectorIntakeFastAskPanel`).
- Hide accordion **§9 Vector Studio** (`isIntakeSectionVisible("vector", 9) → false`).
- Review checkbox, notes, warnings, and saved mapping summary moved into the unified surface.
- `VectorStudioPanel` component retained for potential future non-vector use; not rendered on vector pathway.

For `pathway !== "vector"`:

- Manual: §9 already hidden; no vector workflow forced.
- Quick estimate: §9 hidden; minimal sections only.

---

## Fix / refactor summary (Phase 4)

1. Renamed panel title to **Fișier vector și layere**.
2. Structured sections: Fișier vector → Analiză SVG → Mapare layere → Întrebări rapide → Aplicare → Review status.
3. Added review props: manual review checkbox, review notes, analysis status, saved mappings summary.
4. Hid §9 for vector pathway in `volumetricIntakePathway.ts`.
5. Removed section 9 from `VECTOR_FAST_ASK_SECTIONS` highlight list.
6. Updated pathway card subtitle and hint text.

---

## Data preservation (Phase 5)

- All `product_spec_json` vector fields unchanged.
- `deriveFastAskFromSpec` still rehydrates layers, file metadata, review notes.
- `mapVectorFastAskToProductSpec` unchanged contract (no DB migration).
- Existing intakes (e.g. `IR-MQ3C869E`, `WI-SMOKE-P001`) display saved vector data in unified surface after refresh.

---

## Tests / lint (Phase 6)

```text
volumetricIntakePathway.test.ts — 10 PASS (incl. §9 hidden on vector)
VectorIntakeFastAskPanel.test.tsx — 12 PASS
Product001IntakeSpecEditor.vectorFastAsk.test.tsx — 18 PASS
```

ESLint: 0 errors, 1 pre-existing `react-hooks/exhaustive-deps` warning in `VectorIntakeFastAskPanel.tsx`.

Backend: not touched.

---

## Browser validation (Phase 7)

### A. Volumetric vector — `IR-MQ3C869E`

- Single surface **Fișier vector și layere** visible.
- File `vetro_litere.svg`, analysis status, layer mapping, quick questions, review checkbox present.
- Saved mappings (5) shown in review section.
- Sections 1–8 below for geometry/finish; **no §9 Vector Studio**.
- No fake geometry calculated.

### B. Manual pathway

- Covered by tests: vector surface hidden; `Detalii specificație` label shown.

### C. Quick estimate

- Covered by tests: vector surface hidden; sections 1–2 only.

### D. WI-SMOKE-P001

- Values confirmed in Simulare tab: 4800 / 600 / 60 / 2.88 / 18 / 9.
- Single vector surface; no §9 duplicate.
- Baseline 844,41 EUR preserved via existing volumetric shell / CostEngine tests (no pricing changes).

### E. Generic unresolved — `IR-MQ3E7K2V`

- Stage 0 clean; **Alege tip lucrare**; no vector surface.

### F. /quotes

- Not re-smoked in browser this session; generic QuoteWizard unchanged (no frontend quote-creation code touched).

---

## Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/volumetricIntakePathway.ts` | Hide §9 on vector; update hints |
| `frontend/src/lib/volumetricVectorFastAskMapping.ts` | Remove §9 from highlight sections |
| `frontend/src/components/workos/VectorIntakeFastAskPanel.tsx` | Unified surface + review |
| `frontend/src/components/workos/Product001IntakeSpecEditor.tsx` | Wire review summary props |
| `frontend/src/lib/volumetricIntakePathway.test.ts` | §9 visibility test |
| `frontend/src/components/workos/VectorIntakeFastAskPanel.test.tsx` | Surface section tests |
| `frontend/src/components/workos/Product001IntakeSpecEditor.vectorFastAsk.test.tsx` | §9 hidden tests |
| `docs/qa/BUILD_VECTOR_SINGLE_SURFACE.md` | This document |

---

## Confirmations

- [x] No pricing changes
- [x] No CostEngine changes
- [x] No quote/order created
- [x] No Reference Catalogs started
- [x] No fake geometry calculated
- [x] SVG layer detection preserved
- [x] Manual flow preserved
- [x] Quick estimate preserved
- [x] Vector Studio data preserved in `product_spec_json`
- [x] WI-SMOKE-P001 baseline preserved
- [x] Product001IntakeSpecEditor contract preserved
- [x] Delivery terrain gating unchanged

## Commit

`2777ee9` — refactor: consolidate vector intake surface

## PASS/FAIL

**PASS**
