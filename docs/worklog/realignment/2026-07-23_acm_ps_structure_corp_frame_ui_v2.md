# 2026-07-23 — ACM PS structure UI v2: Corp casetat + Structură metalică

| Field | Value |
|-------|-------|
| **Status** | `ACM_PS_UI_CLOSED` — owner ACCEPT 2026-07-23 evening |
| **Product title** | **Alucobond casetat** |
| **Template code** | unchanged `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| **Supersedes** | 3-card PS nucleus (Față · Casetare · Prinderi) from `2026-07-23_acm_ps_structure_audit_and_ui_v1.md` |

## Owner nucleus

```text
Alucobond casetat
├── Corp casetat     (debitare + V-groove + manoperă pliere · oversized/segmentare)
└── Structură metalică  (cadru Al|oțel · cutlist · prindere interior)
```

### Corp casetat — component truth (owner 2026-07-23)

- **O componentă:** față + laterale + ultimele pliuri = **bond** (ACM/Alucobond), indiferent de nr. de folduri.
- Când **nu** e segmentat: corpul e din **aceeași placă** — gravată (V) și **îndoită**, **niciodată** lipită din piese extra / alt material ca „corp diferit”.
- Seed `face` / `returns` / assembly = linii ops/BOM pe **aceeași** componentă corp — nu corpuri materiale separate.
- Segmentare (MIXED §11) = mai multe panouri-corp din bond (fiecare mono-placă), nu lipire pe laterale.

## Authority cited (not reinvented)

| Topic | Doc |
|-------|-----|
| Corp CNC order | `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` §4 |
| Fixare pe cadru | MIXED §5 |
| Cadru atelier | MIXED §6 + `ACP_INTERNAL_FRAME_OWNER_RULES.md` |
| Panou > foaie | MIXED §11 + nesting contract |

## UI mapping

| Card | Route step | Seed BOM note |
|------|------------|---------------|
| Corp casetat | `/structure/corp-casetat` | face + returns + fasteners = decomposition inside Corp |
| Structură metalică | `/structure/structura-metalica` | `acp_internal_frame` / metal_frame — teaching from OWNER_RULES |

Legacy URLs `fata-panou` · `casetare` · `prinderi-asamblare` → redirect **Corp casetat**.

## Owner clarify — CNC processes (2026-07-23)

Nu se prezintă ca slogan „groove cut fold” fără distincție:

Taxonomie CNC — **3 elemente separate** (owner 2026-07-23):

| # | Etichetă RO | Produs | Sens |
|---|-------------|--------|------|
| 1 | **Decupare** | Litere + ACM | Taie prin |
| 2 | **Canal / Șanfren** | Litere | Canal suprafață/margine (lipire volum) |
| 3 | **V-groove** | Dibond/ACM | Șanț V pentru **îndoire**; piele ~0.8 mm |

ACM Corp: 1+3. Litere față: 1+2. Pliere ACM = manoperă după CNC.

Schițe owner (păstrate + linkuite):

| Schiță | Path |
|--------|------|
| Taxonomie CNC + toate schițele | [`docs/architecture/CNC_PROCESS_TAXONOMY_RO.md`](../../architecture/CNC_PROCESS_TAXONOMY_RO.md) |
| V-groove → pliu Dibond | [`audit_assets/24_acm_vgroove_fold_geometry.png`](./audit_assets/24_acm_vgroove_fold_geometry.png) |
| Canal/Șanfren litere | [`audit_assets/25_letters_canal_sanfren_section.png`](./audit_assets/25_letters_canal_sanfren_section.png) |
| **Literă pe layere** (secțiune) | [`audit_assets/26_letters_volumetric_section_confectionare.png`](./audit_assets/26_letters_volumetric_section_confectionare.png) |
| DXF un pliu 200×30 (ArtCAM) | [`audit_assets/30_acm_un_pliu_200x30_owner.dxf`](./audit_assets/30_acm_un_pliu_200x30_owner.dxf) |
| DXF două pliuri L1=10 / L2=3 cm | [`audit_assets/30_acm_2_pliuri_100x30_owner.dxf`](./audit_assets/30_acm_2_pliuri_100x30_owner.dxf) |
| Doc ArtCAM DXF | [`docs/architecture/ACM_ARTCAM_DXF_OWNER_GOLDEN.md`](../../architecture/ACM_ARTCAM_DXF_OWNER_GOLDEN.md) |

Geometrie V→pliu: 135°/2 mm→45°; **90°/3 mm→90°** (casetă tipică).

## Commercial pricing rule (owner 2026-07-23)

**Niciodată pe oră și nici pe timp** (minute/ore) pentru debitare / V-groove ACM casetat.

| Linie | Bază comercială | Tarif owner |
|-------|-----------------|-------------|
| Debitare (`ACM_PANEL_CUTTING`) | EUR/**ml** (`panel_perimeter_m`) | 1.5 EUR/ml |
| V-groove (`ACM_V_GROOVE`) | EUR/**ml** (`fold_length_m`) | 3.0 EUR/ml |
| Asamblare | EUR/**mp** (min 20 EUR) | 15 EUR/mp |

Timp CNC (minute/ore) = doar EIC / capacitate internă — nu bază CPP/ofertă.  
Seeds: `seed_acm_boxed_mounting_owner_rates.py`, `commercial_rules_volumetric_v2.py`.

## Finishes teaching finalized (2026-07-23)

Display-only on PS detail pages (authority: MIXED §5 / §7 / §8):

| Surface | Content |
|---------|---------|
| **Corp casetat** | Finisaj față ≠ volum; tipuri placă / Oracal 651 / print+lam; strategie folie 1→2→3; calc card `finish-foil` |
| **Structură metalică** | Fixare → colant după; calc card `colant-order` |
| Teaser cards | Corp `· finisaj față/volum`; Frame `· colant după fixare` |

Still gap (next build — owner ACCEPT note): Finish Contract runtime + **finisaje ACM în Intake (neapărat)**.

## Owner ACCEPT package (2026-07-23 evening)

See `2026-07-23_acm_ps_structure_ui_closed.md`:

- UI OK → **CLOSED**
- Finisaje → Intake obligatoriu
- CNC ops seed → nu prioritar; contează pregătire grafică CNC
- Qty pe material desfășurat → da
- SKU profil → DEFERRED confirmat
- Contract path → ACCEPT

## Owner confirm — Corp blank + debitare (2026-07-23)

**Material desfășurat** (atelier / UI) = foaia plată înainte de V/pliere, nu fața finită.  
Repo alias: `blank_*` — **nu** afișa „blank” în UI atelier pentru Alucobond casetat.

Repo terms: `W`/`H` (față), `L1`/`L2` (întoarceri), `fold_count`, `blank_*_mm`.

```text
BW/BH = W/H + 2×(L1[+L2]) + 10 mm cnc_fixing_margin
qty CUT (comercial) ≈ 2×(BW + BH) / 1000  ml   ×  1.5 EUR/ml
```

- Debitare **nu** se calculează doar din dimensiunea feței (proxy `2×(W+H)` = legacy, retras ca autoritate).
- Intrări minime: față + L1 (+ L2 la dublu pliu). Exact producție = traseu CUT măsurat când există.
- Nicodată pe oră / pe timp.

Code: `blankPreviewMm` / `ACM_BLANK_CNC_FIXING_MARGIN_MM` in `alucobondCasedPanelSelection.ts`.  
Doc: `ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md` + commercial geometry deduction v1.

## Owner confirm — cutlist symbol **P** (2026-07-23)

| Item | Status |
|------|--------|
| **P** = outer width of frame profile section (mm) | **OWNER_CONFIRMED** |
| Cutlist: shorts/crossbars = axis − 2×P | **OWNER_CONFIRMED** |
| Concrete profile SKU / default numeric P | **DEFERRED confirmat** la ACCEPT UI (`ACP_INTERNAL_FRAME_OWNER_RULES.md` §1.4) |

Amended: `docs/decisions/ACP_INTERNAL_FRAME_OWNER_RULES.md` §1.2b.

## Boundary

- Display / teaching only — no Aggregate frame BOM, no profile SKU GO, no Composer
- No EUR hardcode on PS pages
- Letters nucleus unchanged

## Decision amendment

`decision__letters_acm_compatibility_composer_direction_v1.md` §9 step 3 updated to this 2-card model.
