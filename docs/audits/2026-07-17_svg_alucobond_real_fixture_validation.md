# Runtime audit — LITERE-VOLUMETRICE-ACP.svg (external)

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Fixture path | `C:\Users\offic\Desktop\fisiere-teste-svg\LITERE-VOLUMETRICE-ACP.svg` |
| In repo | **No** (external only) |
| SHA-256 before | `afce1e6f07ffb9db1ec328aa53898dc76e2b6c461429a5a5605de0b3430d85ba` |
| SHA-256 after | `afce1e6f07ffb9db1ec328aa53898dc76e2b6c461429a5a5605de0b3430d85ba` |
| Bytes | 17827 |
| No-mutation | **PASS** |

## Structure (metadata only — no SVG content copied)

| Item | Value |
|------|-------|
| viewBox | `0 0 2098.04014 734.32606` |
| width/height attrs | `2000.02cm` / `700.018cm` |
| Raw mm from attrs | ~20000 × 7000 (absurd) |
| groups | 1 |
| paths | 2 (7 + 13 closed subpaths) |
| polygons | 1 (4 points, stroke, fill=none) |
| transforms | 0 |

## Detection (analyzer runtime proof)

| Item | Result |
|------|--------|
| closed_contour_count | 21 |
| candidate_count | 21 |
| Top candidate `contour_id` | `cc_60db6024` |
| Top `element_id` | `el-1` |
| Top source type | `polygon` |
| geometry_hash | `60db6024` |
| width_mm (guarded) | 2098.022 |
| height_mm | 734.308 |
| area_mm2 | 1540593.13 |
| perimeter_mm | 5664.658 |
| centroid | (1049.02, 367.16) |
| contains_count | 15 |
| rectangularity_score | 0.7725 |
| confidence | 0.9 |
| is_outer_candidate | true |
| unit_ambiguity | true (`viewbox_as_mm_corel_cm_guard`) |
| Identity reanalysis | stable `contour_id` set |
| Letters separate | path_subpath candidates present; not top |

### Explanation (owner-facing)

```text
Candidat panou: probabil
- contur închis
- suprafață mare (84.9% din compoziție)
- conține 15 elemente
- rectangularitate 0.7725
```

## Confirmed selection sample (typed, not auto-product)

| Field | Value |
|-------|-------|
| role | `ALUCOBOND_CASED_PANEL` |
| fold_count | 2 |
| l1_mm | 60 |
| l2_mm | 25 |
| finished_depth_mm | 60 (= L1 authority) |
| service_corner | `TOP_RIGHT` |
| internal_frame_enabled | true |
| blank preview | 2268.022 × 904.308 mm |

## Boundaries proven

- No Optimize / SVGO on file
- No DXF / CPP / tasking
- Letters not selected as panel (polygon wins)
- Color not used as scoring authority
- Overlay highlight is preview-DOM only

## Visual / UI proof status

| Item | Status |
|------|--------|
| Vitest real-fixture case | PASS |
| Runtime proof JSON | `docs/audits/_runtime_fixture_proof.json` |
| Live FE/BE | `:3000` / `:8001` up during build |
| Click-path screenshots (seeded WS) | **GUARDED** — not captured (no seeded write workspace in this pass) |

Machine-readable dump: `_runtime_fixture_proof.json` (metrics only; no SVG payload).
