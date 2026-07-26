# ACM casetat — Product System audit + UI structure v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Status** | Audit + UI display v1 (after `LETTERS_PS_UI_CLOSED`) |
| **Template** | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| **Owner label** | Panou Alucobond casetat |
| **Gate** | Letters PS closed; Composer/contract still blocked |

---

## 1. Verdict audit

| Dimensiune | Verdict |
|------------|---------|
| **Funcționalitate runtime** | PARTIAL — Intake mounting + AcmPanel wired; PS Structură era BOM brut |
| **Logică calcul** | PARTIAL — formule pe seed (arie, perimetru, fold); rate honesty încă „parțial” |
| **Modularitate** | PARTIAL — 3 componente nucleu clare; applied_content XOR + metal frame optional în dossier; VL pack linked, nu în nucleu |
| **Denumiri** | FRAGMENTED — ACM/ACP/Alucobond/Dibond; cod BOXED vs label casetat |
| **UI PS tip Litere** | Era lipsă → livrat v1 pe 3 pași |

---

## 2. Funcționalitate (ce face template-ul)

### Dual role
1. **Standalone offerable** (`root_offerable: true`) — panou/suport casetat ca produs
2. **Linked child sub Litere** — `optional_addon` / mounting_solution când operator alege montaj ACM

### Nu este
- Cabinet iluminat full (`TPL-ACM-CASSETTED-PANEL` arhivat)
- Litere volumetrice (plexi/cant/Forex/LED litere)
- `MAT-ACP-FATA-LITERE` (plexi — capcană)

### Intake (deja)
- Contur `ALUCOBOND_CASED_PANEL` / `SUPPORT_CONTOUR` → binding template
- `mounting_solution.template_code` + `acm_panel_instance`

---

## 3. Logică (calcul / operații)

| Componentă | Material | Operații cheie | Inputuri tipice |
|------------|----------|----------------|-----------------|
| `comp_acm_panel_face` | `MAT-ACM-BOND-PANEL` (mp) | `CUT_ACM_PANEL` — perimetru × passes(1) | width/height/perimeter/thickness |
| `comp_casetted_returns` | ACM strip / returns | `V_GROOVE_ROUTER` (fold_length_m); `FOLD_CASSETTE` (neprețuit quote) | fold_length, return depth, angle |
| `comp_mounting_fasteners` | `MAT-SURUBURI-GEN` | `ACM_BOXED_ASSEMBLY` (arie); `MOUNT_ACM_PANEL` (neprețuit quote) | panel_area_m2 |

**Notă:** treceri CNC litere (2/3/5) **nu** se aplică aici — ACM cut/V-groove au propriile `passes` pe formule seed (implicit 1 pe cut/V-groove în slice-ul boxed).

---

## 4. Modularitate

```text
Nucleu ACM (3)          Module / contract (nu nucleu structură)
─────────────────       ─────────────────────────────────────
Față panou              applied_content: Letters XOR Logo
Casetare / V-groove     metal_frame optional (operator)
Prinderi / asamblare    Litere pack FACE/BACK/CANT/LED/FINISH (linked)
                        cycle_guard: nu VL root sub ACM dacă VL→ACM
```

Composer Litere↔ACM = **după** acest UI (decision §9).

---

## 5. UI PS v1 (acest build)

Pași structură (puritate ACM):

1. `/structure/fata-panou` — Față panou ACM  
2. `/structure/casetare` — Casetare / V-groove  
3. `/structure/prinderi-asamblare` — Prinderi / asamblare  

Pattern = Litere: Identity · Cum obții · Cum calculăm · Document.  
Display only — fără Product Truth write, fără Composer.

---

## 6. Sources

- `backend/seeds/seed_tpl_acm_boxed_mounting_support_v1.py`
- `backend/scripts/seed_acm_template_pack.py` (`CASSETTED_COMPONENTS`)
- `docs/architecture/ACP_ACM_DIBOND_TERMINOLOGY_MAP.md`
- `docs/worklog/realignment/decision__letters_acm_compatibility_composer_direction_v1.md`
- Letters closed: `2026-07-23_letters_ps_structure_ui_closed.md`
