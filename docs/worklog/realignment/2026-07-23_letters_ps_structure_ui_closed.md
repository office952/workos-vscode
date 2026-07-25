# Letters Product System structure UI — CLOSED

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Status** | `LETTERS_PS_UI_CLOSED` |
| **Owner** | ACCEPT închidere (2026-07-23 evening) |
| **Template** | `TPL-VOLUMETRIC-LETTERS_v2` |
| **Decision link** | [decision__letters_acm_compatibility_composer_direction_v1.md](./decision__letters_acm_compatibility_composer_direction_v1.md) §9 |

---

## 0. Schiță owner — literă pe layere

Secțiune confecționare (față · volum · spate · LED):

- [`audit_assets/26_letters_volumetric_section_confectionare.png`](./audit_assets/26_letters_volumetric_section_confectionare.png)
- Hub CNC + toate schițele: [`docs/architecture/CNC_PROCESS_TAXONOMY_RO.md`](../../architecture/CNC_PROCESS_TAXONOMY_RO.md)

## 1. Verdict

Product System **Structură produs** pentru Litere volumetrice este **închisă** ca UI de documentare / lectură owner.

Nu este închidere Execution / Aggregate / Intake / Pricing. Este închiderea **nucleului Litere pe Product System** (card ≠ task; display SoT pe pagini).

---

## 2. Done (ACCEPT)

| Pas | Rută | Conținut blocat pe UI |
|-----|------|------------------------|
| 1 Vizual față | `/structure/vizual-fata` | plexi, CNC **2 treceri**, finisaj față MAT-*, nesting mp, Cum obții |
| 2 Volum aluminiu | `/structure/volum-aluminiu` | 30/60/80/100, finisaj cant, ml = perimetru față |
| 3 Capac spate | `/structure/capac-spate` | Forex mp + CNC **3** (fără șanfren) / **5** (cu șanfren) |
| 4 Sistem LED | `/structure/sistem-led` | pitch 250, W/modul, light_color, PSU 30%, **fără emblemă** |

Plus pe toate 4:

- Panou **Cum obții · ordine taskuri** (`lettersStructurePrincipalTaskOrder.ts`)
- **Cum calculăm** (formule, fără EUR hardcodat pe pagină)
- Nav chip/rând → detaliu

**Finisaj produs:** rând **ascuns** pe hartă (ACCEPT amendament). Finisaje pe **Față** + **Volum**.

---

## 3. Out of scope (explicit — nu blochează CLOSE)

- Emblemă / casetă densitate mp
- Montaj (bare, ACM, șablon) în nucleu Litere
- Procesor dinamic finisaj → ordine taskuri (→ Intake V6, după ACM)
- Aggregate / Product Definition pe carduri
- Composer + contract Litere↔ACM
- Redeschis Finisaj produs ca orchestrator

---

## 4. Amendament față de decision §9 (text vechi)

| Înainte | ACCEPT acum |
|---------|-------------|
| Finisaje subtile **sub pasul Finisaj** | Finisaj produs **ascuns**; finisaje pe **Față** și **Volum** |

---

## 5. Next (deblocat)

1. UI ACM casetat pe același pattern (puritate, display-only) — `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`
2. Apoi contract schema (docs)
3. Apoi Composer mock

---

## 6. Canonical code (display)

- `frontend/src/features/product-system/letters*StructureDocumentation.ts`
- `frontend/src/features/product-system/Letters*StructureDetailPage.tsx`
- `frontend/src/features/product-system/lettersStructurePrincipalTaskOrder.ts`
- `frontend/src/features/product-system/ProductSystemStructureReadonlyPanel.tsx` (Finisaj hide)
