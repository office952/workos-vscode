# WORKOS_ACM_PANEL_OPERATOR_CONFIGURATION_21ST_UI_AUDIT

**Status:** Audit only — STOP la owner gate  
**Date:** 2026-07-20  
**Workspace runtime:** `IV6-DB2F86B7` (`a7b0162b-dc91-467f-aa24-c1279fb3a073`)  
**Route:** `/intake-v6/a7b0162b-dc91-467f-aa24-c1279fb3a073/operator`  
**Viewport:** 1440×900  
**Evidence:** [`docs/audits/_evidence/2026-07-20_acm-panel-operator-config-ui/`](./_evidence/2026-07-20_acm-panel-operator-config-ui/)  
**Domain commit (conditional PASS prior):** `7c72250271471dba88ff753543cb9096b8b797c1`

---

## 1. Rezumat executiv

Domain-ul `AcmPanel` există și e persistat pe fixture (role confirmed, association/technical **proposed**, composition instance **unconfirmed**, segmented **PROPOSED**). UI-ul **nu** este un configurator sibling pentru `AcmPanel`: panoul e îngropat în Configurare → Montaj → „Fundal și carcasă”, fără axe de stare pe instanță, fără `field_authority`, fără relations editor, fără progressive disclosure pe module inactive.

Recomandarea `component list + inspector + progressive disclosure + sticky preview + compact validation rail` este **susținută de probe** (runtime gap + Figma Finisaje accordion Litere + 21st settings/status/list patterns), dar **nu** e încă implementabilă ca „drop-in”: Figma Montaj actual modelează montaj comercial A/B/C, nu AcmPanel; nested 9-secțiuni permanente ar produce nesting excesiv. Verdict: **direcție validă de proiectare, necesită build UI dedicat după owner GO**.

**Scor direcție stabilită: 57/100** (domain ready ~85, operator-config UX ~40).

---

## 2. Capability inventory

| Capacitate | Disponibilitate | Auth | Scop | Doveadă folosirii | Limitări | Fallback |
|------------|-----------------|------|------|-------------------|----------|----------|
| **21st.dev MCP** (`user-21st`) | ready | signed-in | pattern search | Query-uri reale (secțiunea 14); preview PNG în evidence | metadata free; `get_component` paid — nefolosit | N/A — MCP a funcționat |
| **Figma MCP** (`user-figma`) | ready | ready | audit WorkOS nodes | `get_screenshot` + `get_metadata` + `get_design_context` pe fileKeys (secțiunea 15) | Make files N/A | N/A — MCP a funcționat |
| **Browser / Playwright** | local FE:3000 BE:8003 | guard bypass | edge-to-edge shots | 13 PNG runtime în evidence + `screenshot-index.json` | depinde de stack live | — |
| **Screenshots** | da | — | matrice | `01`…`11b`, `figma-*`, `21st-*` | — | — |
| **Repo / code search** | da | — | surface map | subagent UI map + grep AcmPanel | — | — |
| **API** | `:8003` | local | runtime truth | `runtime-summary.json`, `runtime-truth.json` | top-level `acm_panel_instance` null pe acest WS | nested under mounting |
| **SQL read-only** | available | — | — | **NOT USED** | — | API suficient |
| **Test inventory** | da | — | domain vs UI | Vitest instantiate + pytest coalesce | UI fără teste axe status | — |
| **GitHub** | optional | — | — | **NOT USED** | — | — |
| **Subagenți** | da | — | discovery | UI surface map + UI gap inventory | verdict = agent principal | — |

**Nu există declarații 21st/Figma pe fallback.** Ambele MCP-uri: **USED / PROVEN**.

---

## 3. Workstreams

| WS | Rezultat |
|----|----------|
| W1 Runtime truth | Instance nested, statuses, capabilities, relations, field_authority documentate |
| W2 Screenshots | Matrice 1440×900 pe `IV6-DB2F86B7` |
| W3 21st.dev | 6 query-uri search + 10 preview PNG salvate |
| W4 Figma | 2 fileKeys, 4 noduri screenshot, metadata Montaj, design_context `41:104` |
| W5 Raport | acest document — stop owner gate |

---

## 4. Runtime truth (`IV6-DB2F86B7`)

Sursă: `GET /api/v1/intake-v6/workspaces/a7b0162b-dc91-467f-aa24-c1279fb3a073` → [`runtime-summary.json`](./_evidence/2026-07-20_acm-panel-operator-config-ui/runtime-summary.json)

| Axis | Valoare |
|------|---------|
| SVG | `litere-cu-fundal-acm-segmentat.svg` (UI) |
| `acm_panel_domain_action` | `upsert` |
| Top-level `finish_setup.acm_panel_instance` | **absent** pe acest payload |
| Nested instance | `mounting_solution.configuration.acm_panel_instance` → `acm_cc_7af1352f_ff5c35da170d` |
| Adapter | `SUPPORT_CONTOUR` |
| Template | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| `role_status` | **confirmed** |
| `association_status` | **proposed** |
| `technical_configuration_status` | **proposed** |
| `composition_status` (instance) | **unconfirmed** |
| `svg_support_selection.status` | **proposed** |
| `segmented_background.status` | **PROPOSED** (2 panels) |
| Capabilities active | `boxed_returns`, `rear_lip`, `segmented_panels` |
| Capabilities inactive | cutouts, LED, rear_closure, totem_face, wall/structure mounting, … |
| Relations | 2× `belongs_to_assembly:proposed`; 1× `positioned_on:unknown` |
| Field authority | geometry=`detected`; fold/L1/L2/thickness/frame=`catalog_default` |

**Provenance gap UI vs payload:** pe Straturi, composition strip arată produs „Litere + Panou Alucobond” cu badge **Confirmat**, în timp ce `composition_status` pe instanță rămâne **unconfirmed**. Operatorul poate crede că panoul e „adevăr”, deși axele tehnice/asociere sunt încă proposed.

---

## 5. Audit edge-to-edge

### Shell / header / stepper
- Shell WorkOS intact (sidebar + top bar + stepper Straturi/Configurare/Confirmare).
- Banner sistem „Stare sistem: necesită verificare” + footer „2 avertizări” — vizibile, utile, dar competiție cu decizia de componentă.

### Straturi
- Preview SVG + role cards: Contur suport / Vector Litere — **clar**.
- Hint ACP → „Panou Alucobond casetat” — **bun**.
- Composition panel + offer scope — **prezent**.
- Lipsă: rând sibling „Panou Alucobond” ca componentă configurabilă (doar rol geometrie + warning pe Element 1).

### Configurare
- Tabs Finisaje / Iluminare / Montaj — Litere trăiesc în Finisaje; ACM în Montaj/Fundal.
- Preview sticky din Straturi **nu** rămâne co-primar pe Configurare (prioritate comercială dreapta).
- Nested: Fundal → ACP config → module locale → segmented — **adâncime mare**.

### Warnings / blockers
- Compacte în footer (2 avertizări / 8 info) — pattern bun de păstrat.
- Badge „Propunere” pe Fundal — corect semantic, dar fără mapare la `association_status` / `technical_*`.

### Ce vede operatorul vs intern
| Trebuie văzut | Azi | Intern de ascuns / demote |
|---------------|-----|---------------------------|
| Stare detected→confirmed | parțial (Propunere / Confirmat rol) | template id lung, geometry_hash |
| Dimensiuni + fold defaults | câmpuri editabile | `field_authority` raw keys |
| Segmente propose/confirm | panel list + joints | relation_id-uri |
| Relations mounts_on | **absent** | — |
| Capabilities inactive | **absent** (bine) | nu expune totem/LED ca formă |

---

## 6. Poziția AcmPanel în flow

```text
Astăzi (observat):
Straturi: role SUPPORT → composition CTA
Configurare/Montaj: Fundal și carcasă (fields) + Segmented + module locale
Confirmare: summary (out of deep ACM focus)

Lipsă:
Configurare → sibling row „Panou Alucobond” alături de Litere / Vector Logo
```

**Evaluare structură propusă (9 subsecțiuni nested):**  
Respinsă ca **default expanded tree**. Produce nesting pe nesting (step → tab Montaj → Fundal → 9 accordions). Acceptabilă doar ca **mapă de conținut** în inspector, cu progressive disclosure (1–2 secțiuni deschise).

---

## 7. Ierarhia componentelor

### Variante comparate

| Variantă | Verdict față de probe |
|----------|----------------------|
| Accordion per componentă (ca Finisaje Litere/Emblema din Figma) | **Cea mai compatibilă WorkOS** — deja în Figma `23:3` / `47:145` |
| Master-detail (listă + inspector) | **Susținută** de 21st settings/sidebar/project-detail; potrivită dacă apar ≥2 componente ACM/logo |
| Component list + inspector | **Recomandare de audit** (vezi §19) — verificată, nu implementată |
| Split preview/config | Parțial există pe Straturi; pe Configurare preview e secundar — **îmbunătățire** sticky preview |
| Tabs locale în componentă | **Adapt** pentru Geometrie / Construcție / Segmente / Relatii — nu tabs globale noi |
| Progressive disclosure | **Obligatoriu** — Figma deja colapsează „D · Detalii tehnice”; 21st nested accordion e risc dacă se deschid toate |

---

## 8. Câmpurile și gruparea

Grupare recomandată pentru inspector (conținut, nu UI final):

| Grup | Câmpuri | Authority UX |
|------|---------|--------------|
| Identitate | label, template short, role/assoc/tech/composition chips | read-only chips |
| Geometrie | W×H, bbox summary, unități mm | `detected` badge; edit = confirm |
| Construcție | tip panou, fold_count, L1/L2, grosime, rear lip | `catalog_default` ≠ confirmed |
| Segmente | da/nu, panels[], joints, rost | PROPOSED→confirm (există panel) |
| Material/finisaj | material, grosime, culoare/folie | deferred / authority |
| Structură/montaj | frame, rear closure, wall/structure | inactive până activare |
| Relatii | belongs_to / positioned_on; **nu** auto mounts_on | proposed/unknown |
| Extensibilitate | cutouts, LED, inserts | slots inactive — fără formulare |

---

## 9. State UX

Flux dorit: `detected → proposed → operator confirmed → technically ready`.

| Axis | Runtime | UI azi | Gap |
|------|---------|--------|-----|
| role | confirmed | Confirmat pe card strat | OK |
| association | proposed | „Propunere” pe Fundal (indirect) | nu e explicit „asociere” |
| technical | proposed | câmpuri arată ca editabile „adevăr” | **risc** — defaults catalog |
| composition (instance) | unconfirmed | strip poate arăta Confirmat | **inconsistență** |
| selection | proposed | nu e evidențiat | gap |
| segmented | PROPOSED | chip/panel | OK parțial |

**Regulă UI:** defaults `catalog_default` trebuie etichetate „implicit catalog — necesită confirmare”, niciodată green-ready.

---

## 10. Segment editor

**Există:** `IntakeV6SegmentedBackgroundPanel` — listă panel_1/panel_2, joints, Propunere.  
**Lipsește:** legătură vizuală la `AcmPanelComponentInstance.geometry.panels`, ordine drag, rost edit, confirm care promovează relation `belongs_to_assembly` → confirmed.  
**21st:** `table-edit` (7457) + `segment-group` (6160) — adapt pentru listă densă; respinge vector-editor Figma clone ca owner.

---

## 11. Relations UX

Runtime are 7 relations-ish (3 pe instance). UI **nu** afișează relations.  
Operator are nevoie de: „litere pe panou” (`positioned_on` unknown → confirm/reject), nu de `relation_id`.  
`mounts_on` / `attached_to_structure` trebuie UI explicit (necunoscut/proposed/confirmed) — **nu** auto.

---

## 12. Validation

Păstrează footer compact + smart banner.  
Adaugă rail pe componentă: blockers doar pe axe critical (`contour_association`, fold/L1/L2/thickness) când status ≠ confirmed.  
Respinge badge noise tip 8+ chips pe același header.

---

## 13. Preview

| Context | Azi | Recomandare audit |
|---------|-----|-------------------|
| Straturi | SVG preview puternic | păstrează |
| Configurare | comercial sticky dreapta | sticky **schematic/SVG** lângă inspector AcmPanel |
| Blueprint | absent | slot collapsed până technical confirmed (vezi §17) |

Relația preview ↔ formular e slabă pe Montaj: operator editează mm fără highlight pe segment activ.

---

## 14. 21st.dev research (PROVEN)

### Query-uri exacte
1. `modular component configurator inspector master detail settings`
2. `property panel accordion nested form dense settings`
3. `validation status progression sticky summary sidebar`
4. `master detail split view sidebar list inspector`
5. `technical form nested segment editor relation editor blueprint`
6. `sticky footer actions toolbar summary panel`

### Rezultate cu influență (keep/adapt/reject)

| ID | Component | Preview evidence | Rezolvă | Preluăm | Adaptăm | Respingem | Risc DS paralel | Compat WorkOS |
|----|-----------|------------------|---------|---------|---------|-----------|-----------------|---------------|
| 2618 | settings (ln-dev7) | `21st-settings-2618.png` | listă setări densă | ierarhia list→detail | dark tokens WorkOS | SaaS purple chrome | mediu | bun ca pattern |
| 506 | accordion multi-level (originui) | `21st-accordion-multi-506.png` | nested sections | progressive sections | max 1 nested level | multi-level profund | mediu | OK dacă = Finisaje |
| 8041 | base accordion nested | `21st-accordion-nested-8041.png` | nesting | — | — | **default nesting adânc** | ridicat | slab |
| 2514 | card status list | `21st-card-status-2514.png` | status progression | detected→confirmed steps | map pe axe AcmPanel | motion excesiv | mediu | bun |
| 8248 | project detail view | `21st-project-detail-8248.png` | inspector detail | header status + sections | remove assignees/tags SaaS | layout generic project | mediu | medium |
| 19371 | sidebar searchable | `21st-sidebar-19371.png` | component list | grouped nav + counts | ca listă componente produs | glassmorphism | ridicat | medium |
| 7457 | table edit | `21st-table-edit-7457.png` | segment rows | row edit dens | mm columns | CRM checkboxes | mediu | bun segmente |
| 6160 | segment group | `21st-segment-group-6160.png` | view mode | toggle overview/detail | — | — | scăzut | bun |
| 795 / 19519 | toolbar | `21st-toolbar-*.png` | sticky actions | compact action rail | map pe footer WorkOS existent | floating pill SaaS | mediu | păstrează footer WorkOS |

**Influență concretă asupra recomandării:** 2618+19371+2514 susțin **list + inspector + status progression**; 506/8041 arată că nested accordion e util doar controlat; toolbar 21st **nu** înlocuiește footer-ul WorkOS (Figma footer CTA deja există).

**Generate/take 21st:** **NOT USED** (nu s-a generat take; doar search + preview).

---

## 15. Figma audit (PROVEN)

### Fișiere / noduri inspectate

| FileKey | Node | Acțiune MCP | Evidence |
|---------|------|-------------|----------|
| `0CDPIuqoaZ1OQgNnvNyl1F` | `24:268` AD Montaj 1440×900 | `get_screenshot`, `get_metadata` | `figma-montaj-24-268.png` |
| `0CDPIuqoaZ1OQgNnvNyl1F` | `41:104` Montaj Content | `get_design_context` | structure A/B/C + D collapsed |
| `0CDPIuqoaZ1OQgNnvNyl1F` | `23:3` AD Finisaje | `get_screenshot` | `figma-finisaje-23-3.png` |
| `0CDPIuqoaZ1OQgNnvNyl1F` | `47:145` Litere expanded | `get_screenshot` | `figma-litere-47-145.png` |
| `911Q6oRKcEursrRoT4Qj0h` | `14:2` MASTER audit | `get_screenshot` | `figma-master-14-2.png` |

### Constatări Figma
- **Finisaje** = pattern accordion **Litere / Emblema** + sticky commercial — acesta e modelul de paritate pentru AcmPanel sibling.
- **Montaj** = Pregătire / Extensie / Locație **comercial**, nu configurator AcmPanel; „▸ D · Detalii tehnice” e progressive disclosure corect, dar **nu** conține schema AcmPanel.
- Tokens: dark `#0b101e` / borders `#252f41` / accent blue `#3b82f5` / optional purple — păstrează WorkOS, nu importa 21st themes.
- **Nu s-a creat** fișier Figma nou „doar pentru bifă”.

**Influență:** recomandarea list+inspector se aliniază la Finisaje; **nu** la Montaj A/B/C ca loc canonic pentru AcmPanel.

---

## 16. Matrice keep / adapt / reject

| Element | Pastreaza WorkOS | Imbunatateste WorkOS | Preia 21st | Exploreaza Figma | Respinge |
|---------|------------------|----------------------|-----------|------------------|----------|
| Component rows (Straturi roles) | ✓ | sibling AcmPanel pe Configurare | settings list 2618 | Finisaje Litere accordion | rows SaaS generice |
| Accordions | Finisaje pattern | AcmPanel sections progressive | 506 (1 nivel) | `23:3`, `47:145` | nested profund 8041 |
| Forms tehnice | Fundal fields | authority labels | — | Montaj field density | redesign total |
| Status chips | Propunere / Confirmat | map pe 4 axe instance | card-status 2514 | green/amber tokens | animated badge spam |
| Validation | footer rail | per-component blockers | — | footer CTA Figma | sidebar stats SaaS |
| Preview | Straturi SVG | sticky pe Configurare | — | — | inset media cards |
| Segmented editor | panel existent | bind la instance geometry | table-edit 7457 | — | vector-editor owner |
| Sticky actions | footer Continua | — | toolbar doar idei | Footer CTA | floating overflow pills |
| Summaries | panou operator Straturi | summary AcmPanel în inspector | project-detail header | pricing sidebar existent | duplicate pricing |
| Relations | — | listă confirm/reject | — | — | graph editor complex |
| Advanced options | — | inactive capability slots | disclosure | D collapsed Figma | LED/totem forms acum |

---

## 17. Blueprint placement (readiness only — fără impl)

| Opțiune | Verdict audit |
|---------|---------------|
| Schematic în Configurare (inspector) | **Preferat** — collapsed până `technical_configuration_status=confirmed` |
| Tab separat | risc fragmentare vs Finisaje/Montaj |
| Drawer | OK pentru inspect full |
| Side panel | conflict cu comercial sticky |
| Full-screen | doar debug owner |

**Acum poate afișa:** silhouette panou, W×H, panel_1/2 boxes, joint line (din geometry proposed).  
**Ascuns până confirmare:** cutouts, LED, totem, mounting wall/structure ca „adevăr”, orice claim production-ready.

Blueprint = **read-only projection**, niciodată owner.

---

## 18. Remediation awareness (read-only)

Dry-run istoric (din build anterior): ~20 CFG fără SUPPORT; 2 segmented fără binding; 51 bindings fără instance; 18 P1.

**Noul UI ar ajuta ulterior dacă** expune:
- lipsa instance / binding ca blocker pe rândul AcmPanel;
- association proposed fără selection confirm;
- segmented PROPOSED fără confirm.

**Nu remediem acum.** Fără writes.

---

## 19. Recomandarea unică (verificată, nu implementată)

```text
Configurare
├── Component list (sibling): Litere | Vector Logo | Panou Alucobond | …
├── Inspector (selectat): status axes + sections progressive
│     Geometrie → Construcție → Segmente → Material → Structură/Montaj → Relatii
├── Sticky preview (SVG/schematic slot)
└── Compact validation rail (footer WorkOS + blockers pe componentă)
```

**Verificare:**
- Runtime: AcmPanel nu e sibling → gap confirmat (`04`, `05`, `11`).
- Figma: Finisaje deja e accordion pe componente → pattern nativ (`23:3`).
- 21st: settings + status list + table-edit susțin list/inspector/segments fără a înlocui DS.

**Nu acceptăm** arborele 9-secțiuni permanent nested sub „Configurare produs”.

---

## 20. Implementation slices propuse (post-owner-GO only)

1. **S0** — Surface `acm_panel_instance` top-level + UI read model (status axes) pe Configurare.  
2. **S1** — Sibling row „Panou Alucobond” în component list (parity Finisaje).  
3. **S2** — Inspector Geometrie + Construcție cu `field_authority` labels.  
4. **S3** — Bind Segmented panel → instance geometry + confirm promotes relations.  
5. **S4** — Relations confirm/reject (positioned_on / belongs_to).  
6. **S5** — Sticky preview + compact blockers.  
7. **S6** — Blueprint schematic slot (read-only), gated.

Fără pricing, MULTI, totem, LED forms, remediation writes.

---

## 21. Riscuri

1. Operator ia `catalog_default` ca adevăr confirmat.  
2. Composition UI „Confirmat” vs instance `unconfirmed`.  
3. Instance doar nested → UI fragil.  
4. Montaj Figma comercial ≠ AcmPanel — risc de a forța panoul în A/B/C greșit.  
5. Import 21st ca design system paralel.  
6. Badge noise pe 4 axe + segmented + comercial.

---

## 22. Opinia sinceră

Domain-ul e înaintea UI-ului. Continuați să „completați Fundal și carcasă” fără sibling inspector = datorie UX care va forța operatori să trateze proposed ca truth. Nu e nevoie de redesign general; e nevoie de **ridicarea AcmPanel la același rang vizual ca Litere**, cu disclosure disciplinat. 21st e util ca bibliotecă de patternuri, nu ca skin.

---

## 23. Roadmap checkpoint

| Checkpoint | Stare |
|------------|-------|
| Domain instantiate + preserve/upsert/clear | DONE (`7c72250`) |
| Operator AcmPanel configuration UI | **AUDIT DONE — awaiting owner** |
| Blueprint Nivel 1 | blocked / out of scope |
| Historic remediation | blocked |
| MULTI / totem / LED productization | blocked |

---

## 24. Cat suntem in directia stabilita: **57/100**

| Componentă | Scor |
|------------|------|
| Domain AcmPanel | 85 |
| Runtime fixture usable | 80 |
| Operator discoverability AcmPanel | 35 |
| State honesty (proposed≠confirmed) | 40 |
| Segment UX | 55 |
| Relations UX | 15 |
| WorkOS pattern alignment (Figma Finisaje) | 70 |
| 21st leverage without DS fork | 65 |

---

## Screenshot matrix (obligatorie)

| # | Fișier | Rută / sursă | WS | Secțiune | Observație | Problemă | Concluzie |
|---|--------|--------------|----|----------|------------|----------|-----------|
| 01 | `01-intake-straturi-loaded.png` | `/operator` Straturi | IV6-DB2F86B7 | shell+file | SVG loaded | — | baseline OK |
| 02 | `02-component-list-straturi.png` | Straturi | idem | roles | Contur suport + Vector Litere | AcmPanel nu e row sibling | gap list |
| 03 | `03-acm-montaj-surface.png` | Configurare/Montaj | idem | Montaj | ACM în Fundal | ascuns sub tab | discoverability |
| 04 | `04-acm-fundal-expanded.png` | Montaj Fundal | idem | fields | dims+fold+Propunere | fără authority chips | form dens |
| 05 | `05-segmented-section.png` | Montaj | idem | segmented | panel_1/2 + joints | slab legat de instance | bind needed |
| 06 | `06-field-authority-or-defaults.png` | Montaj | idem | defaults | valores catalog în inputs | arată ca confirmed | label authority |
| 07 | `07-blockers-or-banner.png` | footer | idem | validation | 2 avertizări compact | badge noise global | păstrează rail |
| 08 | `08-composition.png` | Straturi | idem | composition | Confirmat pe produs | vs instance unconfirmed | honesty gap |
| 09 | `09-preview-configurare.png` | Configurare | idem | preview | comercial sticky | SVG nu e co-primar | sticky preview |
| 10 | `10-full-page-straturi.png` | Straturi full | idem | scroll | nesting moderate | — | OK |
| 10b | `10b-full-page-montaj.png` | Montaj full | idem | scroll | nesting Fundal+seg+modules | deep | reduce nest |
| 11 | `11-compare-litere-finisaje.png` | Finisaje | idem | Litere | accordion Litere | AcmPanel absent aici | parity target |
| 11b | `11b-compare-straturi-roles.png` | Straturi | idem | roles | support warning | — | keep hint |
| F1 | `figma-montaj-24-268.png` | Figma `24:268` | — | Montaj AD | A/B/C comercial | nu AcmPanel | nu forța panoul aici |
| F2 | `figma-finisaje-23-3.png` | Figma `23:3` | — | Finisaje | Litere/Emblema | — | pattern sibling |
| F3 | `figma-litere-47-145.png` | Figma `47:145` | — | Litere | expanded group | — | field density |
| F4 | `figma-master-14-2.png` | Figma `14:2` | — | MASTER | audit map | — | context |
| 21st | `21st-*.png` | CDN 21st | — | refs | vezi §14 | — | adapt not fork |

---

## Conditional PASS (domeniu anterior — reconfirmat)

| Cerință | Doveadă |
|---------|---------|
| Hash exact | `7c72250271471dba88ff753543cb9096b8b797c1` |
| preserve / upsert / clear | `frontend/src/lib/intakeV6/acmPanel/instantiate.test.ts` |
| Stale / coalesce | `backend/tests/test_acm_panel_domain_coalesce_v1.py` — 3 passed (re-run audit session) |

---

## Owner gate

**STOP.** Fără implementare UI, fără remediation, fără blueprint.

Așteaptă decizia owner pe:
1. Acceptă recomandarea §19 ca brief pentru următorul build UI?  
2. Prioritizează S0–S2 înainte de segment/relations?  
3. Compune composition Confirmat vs instance `unconfirmed` ca defect separat?
