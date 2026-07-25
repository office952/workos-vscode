# ACM / Dibond — DXF owner golden + ArtCAM settings

| Field | Value |
|-------|--------|
| Status | OWNER_CONFIRMED 2026-07-23 (re-attached Desktop) |
| Models | Panou **200 × 30 cm** (față activă) |
| CNC elements | **Decupare** + **V-groove** (nu Canal/Șanfren) |

## Fișiere

| Model | Desktop (sursă owner) | Fixture test | Evidence copy |
|-------|----------------------|--------------|---------------|
| Un pliu | `C:\Users\offic\Desktop\un-pliu.dxf` | [`backend/tests/fixtures/acm_panel_dxf/un-pliu.dxf`](../../backend/tests/fixtures/acm_panel_dxf/un-pliu.dxf) | [`audit_assets/30_acm_un_pliu_200x30_owner.dxf`](../worklog/realignment/audit_assets/30_acm_un_pliu_200x30_owner.dxf) |
| Două pliuri | `C:\Users\offic\Desktop\2-pliuri-100x30.dxf` | [`backend/tests/fixtures/acm_panel_dxf/2-pliuri-100x30.dxf`](../../backend/tests/fixtures/acm_panel_dxf/2-pliuri-100x30.dxf) | [`audit_assets/30_acm_2_pliuri_100x30_owner.dxf`](../worklog/realignment/audit_assets/30_acm_2_pliuri_100x30_owner.dxf) |

SHA256 Desktop ≡ fixture (2026-07-23 refresh): identical to repo golden.

## Dimensiuni owner

| Caz | Față (W×H) | L1 (primul pliu) | L2 (al doilea pliu) |
|-----|------------|------------------|---------------------|
| Un pliu | **2000 × 300 mm** (200 × 30 cm) | **100 mm** (10 cm) | — |
| Două pliuri | **2000 × 300 mm** | **100 mm** (10 cm) | **30 mm** (3 cm) |

Material desfășurat (fără marja +10 mm CNC din blankPreview):  
`blank ≈ față + 2×(L1[+L2])` → un pliu 2200×500; două pliuri 2260×560 (înainte de relief colț).

## ArtCAM — setări pe trasee (owner)

| Vizual pe DXF | Setare ArtCAM | Proces CNC RO | Repo semantic |
|---------------|---------------|---------------|---------------|
| **Exterior negru** (contur închis) | **Cut outside** | **Decupare** | `CUT` (`ACM_PANEL_CUTTING`) |
| **Dungi / linii roșii** | **V-groove along line** | **V-groove** | `V_GROOVE_L1` / `V_GROOVE_L2` (`ACM_V_GROOVE`) |

Nu e Canal/Șanfren de litere. V-groove = îndoire Dibond; Decupare = tăiere prin material.

## Mapare culoare ACI (interim v1)

Toate entitățile pe `Layer 1` (SPLINE). Semantica = **culoare ACI**, nu nume layer:

| ACI | Semantic |
|-----|----------|
| 256 (ByLayer) / 250 | CUT (negru / cut outside) |
| 1 (red) | V_GROOVE_L1 |
| 242 | V_GROOVE_L2 (doar dublu pliu) |

Cod: `backend/services/acm_aci_semantic_mapping.py`  
Măsurători: plan/worklog production geometry metrics 2026-07-20.

## Cross-links

- Taxonomie CNC RO: [`CNC_PROCESS_TAXONOMY_RO.md`](./CNC_PROCESS_TAXONOMY_RO.md)
- Geometrie V→pliu (PNG): [`audit_assets/24_acm_vgroove_fold_geometry.png`](../worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png)
- Material desfășurat: [`ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md`](./ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md)
- MIXED §4: [`MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md`](./MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md)
