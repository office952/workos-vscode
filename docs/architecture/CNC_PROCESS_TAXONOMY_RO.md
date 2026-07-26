# Taxonomie CNC (RO) — 3 elemente separate

| Field | Value |
|-------|--------|
| Status | OWNER_CONFIRMED 2026-07-23 |
| Code SoT | `frontend/src/lib/cnc/cncProcessTaxonomyRo.ts` |
| Badge litere | `frontend/src/lib/cnc/cncProcessableBadge.ts` |

## Cele 3 elemente

| # | Etichetă RO | Produs | Sens |
|---|-------------|--------|------|
| 1 | **Decupare** | Plexi litere + Dibond/ACM | Taie **prin** material (contur / grafică) |
| 2 | **Canal / Șanfren** | **Doar plexi litere** | Canal pe **suprafață** sau pe **margine** — pentru lipire volum–față; **nu** străpunge |
| 3 | **V-groove** | **Doar Dibond/ACM** (îndoire) | Șanț V pe linia de pliu; lasă piele ~0.8 mm; **nu** = Canal/Șanfren |

Mapări:

- Litere față (plexi): **Decupare** + **Canal / Șanfren**
- Alucobond / Dibond casetat: **Decupare** + **V-groove**
- Pliere ACM = manoperă atelier după CNC — nu e al 4-lea element CNC

---

## Schițe owner (evidence)

### 1. Canal / Șanfren — litere (suprafață vs margine)

![Canal / Șanfren — pe suprafață și pe margine pentru litere](../worklog/realignment/audit_assets/25_letters_canal_sanfren_section.png)

- Fișier: [`docs/worklog/realignment/audit_assets/25_letters_canal_sanfren_section.png`](../worklog/realignment/audit_assets/25_letters_canal_sanfren_section.png)
- Sus: canal în material pe suprafață  
- Jos: canal pe margine (pentru litere / lipire volum)

### 2. Literă pe layere — secțiune confecționare (de ce există canalul)

![Literă pe layere — secțiune confecționare litere volumetrice](../worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png)

- Fișier: [`docs/worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png`](../worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png)
- Alias (același conținut): [`26_letters_litera_pe_layere_sectiune.png`](../worklog/realignment/audit_assets/26_letters_litera_pe_layere_sectiune.png)
- **Literă pe layere** (privită în secțiune): față (plexi) · volum (Al) · spate (Forex) · LED în cavitate.
- Canalul / șanfrenul pe marginea feței există ca volumul să se așeze/lipească pe plexi — **nu** e V-groove Dibond.

### 3. V-groove → pliu (Dibond / Alucobond)

![Geometrie V-groove: unghi șanț, bază plană, piele 0.8 mm, unghi pliu](../worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png)

- Fișier: [`docs/worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png`](../worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png)

| Unghi șanț V | Bază plană | Piele rămasă | Unghi pliu |
|--------------|------------|--------------|------------|
| 135° | 2 mm | 0.8 mm | 45° |
| 90° | 3 mm | 0.8 mm | 90° (casetă tipică) |

### 4. DXF owner golden — ArtCAM (200×30 cm)

Doc dedicat: [`ACM_ARTCAM_DXF_OWNER_GOLDEN.md`](./ACM_ARTCAM_DXF_OWNER_GOLDEN.md)

| Model | DXF evidence |
|-------|----------------|
| Un pliu (L1=10 cm) | [`30_acm_un_pliu_200x30_owner.dxf`](../worklog/realignment/audit_assets/30_acm_un_pliu_200x30_owner.dxf) |
| Două pliuri (L1=10 cm, L2=3 cm) | [`30_acm_2_pliuri_100x30_owner.dxf`](../worklog/realignment/audit_assets/30_acm_2_pliuri_100x30_owner.dxf) |

ArtCAM:

- **Exterior negru** = **Cut outside** → Decupare (`CUT`)
- **Dungi roșii** = **V-groove along line** → V-groove (`V_GROOVE_L*`)

### Index rapid — schițe + DXF

| Evidence | Link |
|----------|------|
| Canal/Șanfren (suprafață + margine) | [25_…](../worklog/realignment/audit_assets/25_letters_canal_sanfren_section.png) |
| **Literă pe layere** (secțiune) | [26_…](../worklog/realignment/audit_assets/26_letters_volumetric_section_confectionare.png) · [alias](../worklog/realignment/audit_assets/26_letters_litera_pe_layere_sectiune.png) |
| V-groove → pliu (PNG) | [24_…](../worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png) |
| DXF un pliu 200×30 | [30_un_pliu](../worklog/realignment/audit_assets/30_acm_un_pliu_200x30_owner.dxf) |
| DXF două pliuri L1=10 / L2=3 cm | [30_2_pliuri](../worklog/realignment/audit_assets/30_acm_2_pliuri_100x30_owner.dxf) |
| Doc ArtCAM DXF | [`ACM_ARTCAM_DXF_OWNER_GOLDEN.md`](./ACM_ARTCAM_DXF_OWNER_GOLDEN.md) |

---

## Cross-links

- MIXED §4 (Corp ACM CNC): [`MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md`](./MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md)
- Blank / material desfășurat ACM: [`ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md`](./ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md)
- ArtCAM DXF golden: [`ACM_ARTCAM_DXF_OWNER_GOLDEN.md`](./ACM_ARTCAM_DXF_OWNER_GOLDEN.md)
- Worklog ACM PS: [`../worklog/realignment/2026-07-23_acm_ps_structure_corp_frame_ui_v2.md`](../worklog/realignment/2026-07-23_acm_ps_structure_corp_frame_ui_v2.md)
