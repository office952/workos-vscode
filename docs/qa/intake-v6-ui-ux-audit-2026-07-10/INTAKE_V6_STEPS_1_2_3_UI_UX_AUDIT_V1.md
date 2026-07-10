# Intake V6 — UI/UX Audit Pas 1, 2, 3 (V1)

**Date:** 2026-07-10  
**Status:** PASS_AUDIT_COMPLETE  
**Scope:** Audit only — no implementation

---

## 1. Verdict

**PASS_AUDIT_COMPLETE**

Audit runtime complet pe workspace real, cu capturi pentru Pașii 1–3, toate taburile Pas 2, stări colapsate/expandate, inventar badge-uri, recomandare unică și livrabil Figma.

---

## 2. Runtime auditat

| Field | Value |
|-------|-------|
| URL | http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator |
| Ruta listă cereri | http://127.0.0.1:3000/intake |
| Workspace ID | `22ef834d-f2d0-453b-a7a7-118928c98a39` (UI: IV6-189D2F12) |
| Template | Litere volumetrice (`TPL-VOLUMETRIC-LETTERS_v2`) |
| Fixture | `gradi-curat.svg` — 6 straturi, 5 culori, litere + artwork |
| Backend | :8000 — 200 |
| Frontend | :3000 — 200 |

---

## 3. Figma delivery

| Item | Value |
|------|-------|
| File | WorkOS Intake V6 — UI Audit |
| URL | https://www.figma.com/design/911Q6oRKcEursrRoT4Qj0h |
| File key | `911Q6oRKcEursrRoT4Qj0h` |
| Pagini | 00–10 (overview, current, badge/collapse inventory, proposed hierarchy, tabs system, comparison) |
| Frames | Overview + findings, Tabs & Status System, Proposed Step 2 hierarchy |
| Screenshots repo | `docs/qa/intake-v6-ui-ux-audit-2026-07-10/screenshots/` (24 capturi + manifest) |

---

## 4. Scoruri

| Dimensiune | Scor |
|------------|------|
| Pas 1 | **6.5 / 10** |
| Pas 2 | **5.5 / 10** |
| Pas 3 | **6.0 / 10** |
| Taburi (Pas 2) | **6.0 / 10** |
| Collapsible content | **5.0 / 10** |
| Badge / noise control | **4.0 / 10** |
| **Overall** | **5.7 / 10** |

**Cel mai mare risc:** Blocker-e operaționale ascunse sub „Detalii tehnice” / form-system diagnostics — operatorul vede preț live și tab Finisaje, dar nu vede imediat codurile `SELECTED_LAYER_REFS_MISSING` etc.

**Cea mai mare oportunitate:** Reducerea badge-urilor și consolidarea statusului la nivel de tab + footer issues — câștig rapid de claritate fără schimbare logică.

---

## 5. Cele mai importante 10 probleme

| # | ID | Severitate | Problema |
|---|-----|------------|----------|
| 1 | P2-COL-01 | **Critical** | BLOCKERS SUMMARY (coduri tehnice) este în accordion „Detalii tehnice”, sub fold — risc omisiune blocker |
| 2 | P2-TAB-01 | **High** | 3 surse paralele de probleme: badge Finisaje „2”, footer „Probleme (8)”, form-system blockers |
| 3 | P3-01 | **High** | Pas 3: badge-uri „De completat” x3 + banner „Confirmă compoziția” duplică mesajul de blocare |
| 4 | P1-01 | **High** | Pas 1: triplu semnal complet — check pe fiecare layer + „Toate straturile confirmate” + bară 100% |
| 5 | P2-COL-02 | **High** | Layer cards expandate adaugă badge „651 COLORED” redundant față de dropdown Oracal 651 |
| 6 | P2-NAV-01 | **High** | Calcul live + filtre TOATE/MATERIALE/SERVICII/MANOPERĂ domină vizual tab-ul Finisaje |
| 7 | P1-02 | **Medium** | Panou „Atenție analiză” — 6 chip-uri pseudo-color repetă gruparea din carduri |
| 8 | P2-TAB-02 | **Medium** | Badge „ON” pe tab Iluminare repetă toggle LED activ din conținut |
| 9 | P3-COL-01 | **Medium** | Accordion „Rezumat operator” colapsat nu arată sumar valorilor critice |
| 10 | P1-03 | **Medium** | Carduri layer afișează ID-uri tehnice Product System în fluxul operator |

---

## 6. Audit Pas 1 (Straturi)

### Ce funcționează
- Upload SVG evident, preview mare, metadata compactă (dimensiuni, straturi, culori).
- Decizii straturi cu dropdown „Rol producție” clar.
- Taxonomie owner respectată: „Vector Litere” pe straturi litere.
- CTA principal „Continuă la Review” vizibil.

### Findings

| ID | Zona | Problema | Sev | Recomandare |
|----|------|----------|-----|-------------|
| P1-01 | Panou operator | Progres 100% + buton verde + check pe fiecare card = redundant | High | Păstrează un singur semnal complet la nivel panou; elimină check-urile per-card când toate confirmate |
| P1-02 | Atenție analiză | 6 chip-uri color repetă numele layer | Medium | Transformă în listă text sau collapse cu count „6 grupări detectate” |
| P1-03 | Card layer | `TPL-VOLUMETRIC-LETTERS_v2` vizibil operator | Medium | Mută sub „Detalii” sau helper text discret |
| P1-04 | Metrici tehnice | Accordion corect clasificat (F — advanced) | Low | Default collapsed — OK |
| P1-05 | Sidebar vs main | Panou operator sticky util | Low | Keep |

**Screenshot:** `01_step1_full.png`, `05_step1_layers_expanded.png`

---

## 7. Audit Pas 2 (Review)

### Taburi

| Tab | Scop | Claritate | Obligatoriu | Badge actual | Status recomandat | Probleme | Recomandare |
|-----|------|-----------|-------------|--------------|-------------------|----------|-------------|
| Finisaje | Față, cant, artwork, spate | 7/10 | Da | Pending count „2” | Necesită atenție (1 număr) | Badge + footer 8 + blockers ascunse | Un singur count în tab; blockers în banner top |
| Iluminare | LED, backing | 8/10 | Parțial | „ON” pill cyan | Complet sau Informativ | ON redundant cu toggle | Elimină badge ON; check discret pe tab când complet |
| Montaj | Șablon, sistem montaj | 7/10 | Da | — | Complet / Necesită atenție | Câmpuri dense | Sumar collapsed pe câmpuri completate |

### Collapsibles (Pas 2)

| Secțiune | Tab | Default | Critice ascunse? | Clasificare | Sumar recomandat | Acțiune |
|----------|-----|---------|------------------|-------------|------------------|---------|
| Layer cards (Vector Litere) | Finisaje | Collapsed | Parțial — confirmare | **B** | Nume + Oracal + cant + ✓ | Keep collapsed; remove badge 651 COLORED |
| Layer cards (Vector Logo) | Finisaje | Collapsed | Da — confirm artwork | **A** | Auto-expand primul neconfirmat | Expand first pending |
| Detalii tehnice | All | Collapsed | **Da — blockers** | **A** | „3 blockers · 5 warnings” | **Deschide implicit dacă blockers > 0** |
| Form system backbone | All | Collapsed | Da (dev-facing) | **F** | „Diagnostic tehnic (read-only)” | Rename + default collapsed |
| Calcul live details | Sidebar | Partial | Nu | **C** | Preț total suficient | Keep |

**Screenshots:** `10_step2_full_initial.png`, `11_step2_tab_*`, `13_step2_finisaje_cards_expanded.png`, `15_step2_technical_expanded.png`, `16_step2_form_system_expanded.png`

---

## 8. Audit Pas 3 (Confirmare)

Pas 3 **nu are sub-taburi** — layout vertical cu dashboard + accordions. Evaluat ca „taburi” = secțiuni principale.

| Secțiune | Scop | Suprapunere Pas 2 | Probleme | Recomandare |
|----------|------|-------------------|----------|-------------|
| Rezumat produs | Verificare module | Da — finisaje/LED | Badge De completat x3 | Grupează într-un singur mesaj „3 module de completat în Review” |
| Modular form awareness | Contract form | Parțial | Badge Inclus/Activ/De completat | Reduce la 1 status per modul |
| Handoff panel | Draft boundary | — | Duplicate „Handoff blocat” | Un singur badge blocker |
| Detalii tehnice complete | Debug/readiness | Da | Nested accordions | Flatten 1 nivel |

**Screenshots:** `20_step3_full_initial.png`, `21–24_step3_*`

---

## 9. Badge reduction audit

### Inventar (sample runtime + code trace)

| Pas | Tab | Zona | Text badge | Culoare | Semnificație | Acțiune | Repetă? | Necesar | Rec |
|-----|-----|------|------------|---------|--------------|---------|---------|---------|-----|
| 1 | — | Fișier | gradi-curat.svg | Green | Fișier încărcat | Nu | Nu | Parțial | Replace → text |
| 1 | — | Layer card | ✓ confirmat | Green | Confirmat | Nu | Da x6 | Parțial | Remove când 100% |
| 1 | — | Atenție analiză | pseudo maria (blue) etc | Yellow chips | Grup detectat | Nu | Da | Nu | Remove/Merge |
| 1 | — | Panou operator | Toate confirmate | Green btn | Complet | Nu | Da | Da | Keep (1x) |
| 2 | Finisaje | Tab | 2 | Amber | Pending count | Da | Nu | Da | Keep |
| 2 | Iluminare | Tab | ON | Cyan | LED activ | Nu | Da (toggle) | Nu | Remove |
| 2 | Finisaje | Layer header | OK / Lipsă | Green/Amber | Confirmare | Da | Da | Parțial | Icon only |
| 2 | Finisaje | Expanded | 651 COLORED | Purple | Catalog hint | Nu | Da | Nu | Remove |
| 2 | — | Footer | Probleme (8) | Neutral | Issues count | Da | Parțial | Da | Keep |
| 2 | — | Form system | SELECTED_LAYER_REFS_MISSING etc | Red | Blocker code | Nu | Da x8+ | Parțial | Merge → 1 banner |
| 2 | Sidebar | Calcul | TOATE/MATERIALE/... | Teal chips | Filter | Da | Nu | Parțial | Replace → tabs text |
| 3 | — | Header | Handoff blocat x2 | Orange | Blocker | Nu | Da | Da | Merge → 1 |
| 3 | — | Module rows | De completat | Orange | Incomplete | Da | Da x3 | Parțial | Merge message |
| 3 | — | Module rows | Activ | Green | Active | Nu | Da | Parțial | Text only |
| 3 | — | KPI | Fișier SVG analizat | Teal | Info | Nu | Nu | Nu | Remove |

### Summary

| Metric | Value |
|--------|-------|
| Total badge-uri identificate (Pas 1–3) | ~52 distinct instances |
| Max simultan vizibil (Pas 2 Finisaje) | ~47 |
| Duplicate clare | ON+toggle, De completat x3, Handoff x2, check per layer + 100% |
| Recomandate eliminare | ~18 |
| Recomandate merge | ~12 |
| Recomandate păstrare | ~8 critice |
| **Reducere estimată** | **~45%** |

---

## 10. Direcția unică recomandată

**„Status la nivel de secțiune, nu la nivel de câmp”**

1. **Pas 1:** Un singur semnal complet în panou operator; chip-uri analiză → text count.
2. **Pas 2 tabs:** Finisaje = număr pending; Iluminare/Montaj = check discret; fără ON pill.
3. **Collapsed summaries:** Titlu + valoare principală + 1 secundar + stare (Complet / Necesită atenție).
4. **Blockers:** Banner fix sub tab bar când există blockers — nu doar în accordion tehnic.
5. **Diagnostics:** Form-system / blockers summary → secțiune „Diagnostic tehnic”, collapsed default.
6. **Pas 3:** Un mesaj consolidat „X module incomplete — revino la Review > Finisaje” în loc de 3 badge-uri orange.

Figma frames: paginile **07**, **09**, **00** din fișierul audit.

---

## 11. Owner visual verification

| Check | Path |
|-------|------|
| Pas 1 complet | URL de mai sus → click „Straturi” → vezi 100% + 6 layers confirmate → `01_step1_full.png` |
| Pas 2 tab Finisaje pending | Review → tab Finisaje badge „2” → `10_step2_full_initial.png` |
| Pas 2 blockers ascunse | Review → scroll jos → expand „Detalii tehnice” → BLOCKERS SUMMARY → `15_step2_technical_expanded.png` |
| Pas 2 Iluminare ON redundant | Tab Iluminare → badge ON + toggle LED → `11_step2_tab_iluminare_top.png` |
| Pas 3 incomplete | Confirmare → badge „De completat” pe Față/Cant/Spate → `20_step3_full_initial.png` |
| Figma | https://www.figma.com/design/911Q6oRKcEursrRoT4Qj0h → pagina 00 Audit Overview |

---

## 12. Fișiere atinse

- `docs/worklog/realignment/2026-07-10_intake_v6_steps_1_2_3_figma_ui_ux_audit.md`
- `docs/qa/intake-v6-ui-ux-audit-2026-07-10/INTAKE_V6_STEPS_1_2_3_UI_UX_AUDIT_V1.md`
- `docs/qa/intake-v6-ui-ux-audit-2026-07-10/capture-audit-screenshots.mjs` (script captură — nu runtime app)
- `docs/qa/intake-v6-ui-ux-audit-2026-07-10/screenshots/*` (24 PNG + manifest)

**Nu s-a modificat:** frontend, backend, DB, seed, migrări, pricing, ProductDefinition.

---

## 13. Blocaje și decizii owner

| Decizie | Întrebare |
|---------|-----------|
| Blockers visibility | Blockers operaționale rămân în form-system sau se promovează în banner operator? |
| Pas 3 module badges | Păstrăm granularitate per modul sau un singur mesaj consolidat? |
| Calcul live | Rămâne permanent vizibil pe desktop sau collapsible? |
| Diagnostic tehnic | Acces doar admin/dev sau vizibil operator? |

---

## 14. Next safe step

**Owner review al auditului și selectarea explicită a recomandărilor care primesc GO pentru implementare.**

---

## 15. Părerea sinceră a auditorului

**Ce e deja bun:** Fluxul în 3 pași e clar; preview SVG excelent; tab Finisaje cu layer cards collapsed au sumar util (Oracal + cant); calcul live e valoros pentru operator.

**Cel mai obositor:** Suprapunerea statusurilor — badge, footer, banner, check, pill ON, chip pseudo-color — pe aceeași ecran fără ierarhie.

**Unde se pierde operatorul:** Sub fold-ul „Detalii tehnice” / form-system, unde apar blockers cu coduri englezești, în timp ce prețul live sugerează „totul e OK”.

**Badge-urile:** În majoritate încurcă; ajută doar pending count pe tab Finisaje și footer issues count.

**Tabs + accordions:** Prea adânci la Pas 2 (Tab → Card → Accordion → Sub-card → Badge-uri). Pas 3 e mai flat — direcție bună.

**Schimbarea cu cel mai mare câștig:** Banner unic blocker + eliminare badge-uri redundante (ON, 651 COLORED, check per layer când 100%).

---

## 16. Delivery footer

```
Status: PASS_AUDIT_COMPLETE
Scope respected: YES
Implementation performed: NO
Figma audit completed: YES
Screenshots completed: YES (24)
Worklog: docs/worklog/realignment/2026-07-10_intake_v6_steps_1_2_3_figma_ui_ux_audit.md
Commit: none (audit artifacts untracked unless owner requests)
Owner GO required for implementation: YES
```

---

## Roadmap awareness

**Roadmap awareness: 9/10**

**Poziționare:** Audit UI/UX Intake V6 înainte de orice implementare de simplificare vizuală — aliniat cu fluxul REQUEST → INTAKE V6 → ProductDefinition.

**Direcție stabilită: 95/100%**

**Dead pieces check:**
- Componente UI redundante identificate (badge ON, 651 COLORED, triple complete signals) — documentate, neșterse
- Badge-uri fără rol identificate — propuse eliminare, neimplementate

**Forbidden scope:** respectat — fără pricing/CostEngine/ProductDefinition/DB/seed/implementare.
