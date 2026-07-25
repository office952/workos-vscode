# ACM Product System structure UI — CLOSED

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Status** | `ACM_PS_UI_CLOSED` |
| **Owner** | ACCEPT (2026-07-23 evening) |
| **Template** | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| **Product title** | **Alucobond casetat** |
| **Decision link** | [decision__letters_acm_compatibility_composer_direction_v1.md](./decision__letters_acm_compatibility_composer_direction_v1.md) §9 |

---

## 1. Verdict

Product System **Structură produs** pentru Alucobond casetat este **închisă** ca UI de documentare / lectură owner.

Nu este închidere Execution / Aggregate complet / Composer. Este închiderea **nucleului ACM pe Product System** (2 carduri; display SoT).

---

## 2. ACCEPT — ce e blocat

| Pas | Rută | Conținut |
|-----|------|----------|
| 1 Corp casetat | `/structure/corp-casetat` | material desfășurat · Decupare + V-groove · pliere · finisaj față/volum teaching · oversized |
| 2 Structură metalică | `/structure/structura-metalica` | cadru Al/oțel · P · cutlist · fixare → colant după |

Plus: taxonomie CNC, schițe, DXF ArtCAM, formule blank/CUT — vezi `2026-07-23_acm_ps_structure_corp_frame_ui_v2.md`.

---

## 3. Owner clarificări la ACCEPT (2026-07-23)

| # | Subiect | Decizie owner |
|---|---------|----------------|
| UI | PS ACM display | **OK — ACCEPT** |
| Finisaje | Runtime | **Obligatoriu în Intake** (Finish Contract pe shell) — următorul build prioritar |
| Operații CNC în seed/task_rules | Ordine ops DAG | **Nu contează acum** — contează **pregătirea graficii CNC** (DXF/ArtCAM: Cut outside + V-groove along line) |
| Qty Decupare | Calcul | **Da** — pe material desfășurat (nu doar față) |
| Profil cadru SKU | Default P numeric | **Confirmat DEFERRED** (P ca simbol rămâne; SKU ulterior) |
| Contract / Composer | După ACCEPT ACM | **ACCEPT** să treacă la pasul următor din decision §9 (contract draft) |

---

## 4. Next (după acest CLOSE)

1. **Finish Contract / finisaje ACM în Intake** (neapărat)  
2. Qty Decupare pe material desfășurat pe calea comercială  
3. **Contract schema draft** Litere↔ACM (docs)  
4. Composer — după contract  
5. SKU profil cadru — când owner GO separat  

---

## 5. Evidence

- `2026-07-23_acm_ps_structure_corp_frame_ui_v2.md`
- `docs/architecture/CNC_PROCESS_TAXONOMY_RO.md`
- `docs/architecture/ACM_ARTCAM_DXF_OWNER_GOLDEN.md`
