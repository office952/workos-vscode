# WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_HANDOFF

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Status | **Handoff only** — backlog de căutări 21st.dev; **fără** selecție design final, **fără** implementare |
| Next audit | `WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_AUDIT` |
| Domain authority | [`2026-07-20_WORKOS_PRODUCT_CONFIGURATION_AND_BLUEPRINT_READINESS_AUDIT.md`](./2026-07-20_WORKOS_PRODUCT_CONFIGURATION_AND_BLUEPRINT_READINESS_AUDIT.md) |
| Prior UI / 21st context | [`2026-07-20_WORKOS_UI_SYSTEM_AND_21ST_INTEGRATION_AUDIT.md`](./2026-07-20_WORKOS_UI_SYSTEM_AND_21ST_INTEGRATION_AUDIT.md) |
| Prerequisite truth | `727430b` SVG truth repair — PASS owner; ACM instantiation build closed forward CFG gap (see `INTAKE_V6_ACM_COMPONENT_INSTANTIATION_AND_RELATIONSHIP_V1`) |

---

## 0. Rolul 21st.dev în pasul următor

| 21st.dev este | 21st.dev **nu** este |
|---------------|----------------------|
| Accelerator de UI / pattern library | Sursă de Product Truth |
| Input pentru layout, densitate, affordances | Owner al Panoului Alucobond / segmente / bindings |
| Candidate patterns de adaptat pe dark WorkOS | Contract pentru `ProductAssemblyBlueprintReadModel` |
| Referință de interacțiune (expand, rail, sticky) | Motiv să rescrii ownership sau remediation |

**Ordine de autoritate (neschimbată):**  
runtime WorkOS → Product Truth / composition contracts → Intake V6 patterns acceptate → charter/tokeni WorkOS → 21st.dev → sketch/demo.

Nu decide ownership, blueprint SoT sau remediation din componente demo.

---

## 1. Zone operaționale confirmate (din auditul de configurare)

Aceste zone sunt **confirmate ca probleme/nevoi de UI**, nu ca design final:

1. Configurare modulară: Litere / Vector Logo / Panou Alucobond ca siblings.
2. Panou Alucobond = component row; segmente = children expandabile.
3. Stări detectat → propus → confirmat (rol, binding, segmented, composition) — **domain now separates** `role_status` / `association_status` / `technical_configuration_status` / `composition_status` on `AcmPanelComponentInstance`.
4. Preview ansamblu 2D + viitor blueprint schematic Nivel 1 (read-only).
5. Validation rail pentru gap-uri CFG (support fără SUPPORT_CONTOUR, etc.).
6. Layer list + provenance.
7. Relații **generice** (`positioned_on` / `belongs_to_assembly`; `mounts_on` doar operator) — nu letter-only.

### Domain-ready după ACM instantiation (căutări 21st prioritare)

| Pattern | De ce acum |
|---------|------------|
| Sibling component rows | ACM composition item + instance id stabil |
| Expandable segments | `panels[]` nested under AcmPanel |
| Technical component inspector | `field_authority` + critical/optional/informational |
| Relation editor | generic `ComponentRelation` + status |
| Blueprint preview | geometry/bbox/panels/relations/provenance pe instanță |
| Detected/proposed/confirmed states | axe separate pe instanță |
| Validation rail | CFG gapuri + catalog_default ≠ confirmed |
| Dense technical forms | casing/thickness proposed, not auto-confirmed |
8. Form tehnic dens (thickness, depth, finish, structure) pe shell ACM.
9. Side-by-side configuration + preview.
10. Sticky actions (confirm composition / confirm segmented / continue).

---

## 2. Backlog clar de căutări 21st.dev

Pentru auditul următor: **caută, evaluează, mapează** — nu alege skin final și nu porta.

---

### S1 — Configurare modulară de componente

| | |
|--|--|
| **Problema WorkOS** | Composition afișează Litere + Panou ca sugestie, dar panoul nu arată ca sibling instanțiat; segmentele riscă să pară produse separate. |
| **Pattern căutat** | Modular product / BOM-style component composer: listă de părți ale aceluiași produs, add/optional modules, role labels. |
| **Criterii de acceptare** | Un produs, N componente sibling; optional modules vizibile; fără „plan cards” SaaS; suport pentru status per rând. |
| **Risc design system paralel** | Mediu — demos deseori white cards + marketing hierarchy. |
| **Adaptat la WorkOS** | Dark `v6.card`; labels RO; template codes (`TPL-ACM-…`); composition recommendation/confirmation ca date reale. |
| **Nu copia din demo** | Pricing tiers, „Add seat”, empty marketing CTAs, fake module marketplace. |

**Search hints:** `product configuration modules`, `bom composer`, `optional add-on list`, `configurable product parts`.

---

### S2 — Accordion / expandable operational rows

| | |
|--|--|
| **Problema WorkOS** | Panou Alucobond trebuie să expună Segmente / Structură / Finisaj / Prindere fără a părăsi rândul de componentă. |
| **Pattern căutat** | Dense accordion / expandable table rows (collapsed summary + expanded technical sections). |
| **Criterii de acceptare** | Collapsed: nume + status + dims cheie; expanded: nested children + form sections; keyboard expand; nu full-page jump. |
| **Risc design system paralel** | Scăzut–mediu (shadcn Accordion există deja). |
| **Adaptat la WorkOS** | Densitate Intake V6 (12px); nested `panels[]` sub un singur parent ACM; nu N accordioane = N produse. |
| **Nu copia din demo** | Large padding SaaS FAQ; animated fluff; one-section-per-page wizards. |

**Search hints:** `dense accordion table`, `expandable settings rows`, `nested configuration accordion`.

---

### S3 — Component inspector

| | |
|--|--|
| **Problema WorkOS** | Ownership tehnic (material, grosime, volum, finisaj, structură) e fragmentat; operatorul nu are un inspector pe componenta selectată. |
| **Pattern căutat** | Right/side inspector panel bound to selected entity (properties + status + provenance). |
| **Criterii de acceptare** | Selection sync cu listă/preview; read-only vs editable clar; câmpuri absente = explicit empty/unknown, nu defaults ascunse. |
| **Risc design system paralel** | Mediu — IDE-like chrome poate lupta cu AppShell. |
| **Adaptat la WorkOS** | Inspector pe dark; citește binding/mounting/segmented; gate pe CONFIRMED vs PROPOSED. |
| **Nu copia din demo** | Figma-like property noise; AI chat sidebar; mock property trees fără mapare la finish_setup. |

**Search hints:** `properties inspector panel`, `selected item details drawer`, `entity inspector`.

---

### S4 — Geometry preview

| | |
|--|--|
| **Problema WorkOS** | CCC/panels au geom; layers au W×H dar bbox/xy slab; operatorul are nevoie de preview 2D al ansamblului, nu doar liste. |
| **Pattern căutat** | Canvas/SVG stage cu highlight pe selecție, fit-to-view, overlay labels. |
| **Criterii de acceptare** | Zoom/pan minimal; highlight component/segment; dims callouts opționale; nu editează geometria în v1. |
| **Risc design system paralel** | Mediu — toolbars „design tool” grele. |
| **Adaptat la WorkOS** | Consumă analysis CCC + segmented panels; unit mm; badge detected/proposed. |
| **Nu copia din demo** | Full vector editor, bezier tools, collaborative cursors, stock illustration backgrounds. |

**Search hints:** `svg canvas preview`, `geometry viewer overlay`, `selectable shapes stage`.

---

### S5 — Blueprint schematic viewer

| | |
|--|--|
| **Problema WorkOS** | Nivel 1 blueprint e dorit ca **read model** pentru ofertare/verificare compoziție — nu manufacturing. |
| **Pattern căutat** | Read-only schematic / assembly diagram viewer: colored parts, legend, dimension callouts, relationship markers. |
| **Criterii de acceptare** | Read-only; legendă; stări detected/confirmed; callouts overall + component; zero CUT/FOLD/DXF affordances. |
| **Risc design system paralel** | Ridicat — demos CAD/tech drawing atrag scope creep Nivel 2/3. |
| **Adaptat la WorkOS** | Mapare strictă pe viitorul `ProductAssemblyBlueprintReadModel`; Alucobond = un nod, segments = children. |
| **Nu copia din demo** | CNC nesting UI, G-code, layer blend modes, print-ready title blocks, fake BOM export. |

**Search hints:** `assembly schematic viewer`, `exploded view diagram read-only`, `annotated 2d assembly`, `parts legend diagram` — **exclude** `dxf`, `nesting`, `cam`.

---

### S6 — Layer list

| | |
|--|--|
| **Problema WorkOS** | Straturi = roluri + provenance; trebuie listă operațională densă, nu gallery. |
| **Pattern căutat** | Dense layer/tree list with role chips, visibility, selection sync to preview. |
| **Criterii de acceptare** | Role chip; confirmed state; provenance secondary line; sync highlight cu preview; support vs face vs artwork distinct. |
| **Risc design system paralel** | Scăzut. |
| **Adaptat la WorkOS** | `layer_role_setup` + `sourceGroupIds`/`elementIds`; RO labels; nu inventa roluri din UI. |
| **Nu copia din demo** | Photoshop-like blend/opacity stack ca produs; drag-reorder care rescrie truth fără persist path. |

**Search hints:** `layer list ui`, `dense tree list roles`, `design layers panel compact`.

---

### S7 — Validation rail

| | |
|--|--|
| **Problema WorkOS** | Gap CFG (segmented fără SUPPORT_CONTOUR), composition neconfirmată, bindings lipsă — trebuie scanabile, cu jump-to-fix. |
| **Pattern căutat** | Sticky/side validation rail: blockers / warnings / infos, click-to-focus field/section. |
| **Criterii de acceptare** | Severity order; count badges; scroll-to-target; nu blochează preview; mesaje mapate pe coduri WorkOS. |
| **Risc design system paralel** | Mediu — lime/neon rails din sketch anterior. |
| **Adaptat la WorkOS** | Tokeni semantic WorkOS; logică din demo live-blockers (funcțional), skin dark; coduri tip `SUPPORT_WITHOUT_BINDING`. |
| **Nu copia din demo** | Fluorescent OS ca limbaj global; toast spam; modal wall per warning. |

**Search hints:** `form validation sidebar`, `issue list rail`, `accessibility errors panel`, `sticky form blockers`.

---

### S8 — Detected / proposed / confirmed states

| | |
|--|--|
| **Problema WorkOS** | Același fapt (panou, segment, rol) apare pe mai multe path-uri; UI trebuie să arate authority, nu un singur „verde”. |
| **Pattern căutat** | Tri-state / multi-state chips: detected → proposed → confirmed (+ missing/unknown). |
| **Criterii de acceptare** | Maxim 4–5 stări vizuale stabile; consistente pe rows, inspector, blueprint; nu confunda „suggested composition” cu „component CONFIRMED”. |
| **Risc design system paralel** | Ridicat dacă fiecare modul inventează badges. |
| **Adaptat la WorkOS** | Unifica cu StatusBadge / SourceBadge DS; mapare la `PROPOSED`/`CONFIRMED`/`operator_confirmed`. |
| **Nu copia din demo** | Git PR review colors ca metaforă; gamification progress rings; AI „confidence %” fake. |

**Search hints:** `status chips workflow`, `draft proposed published badges`, `review state indicators`.

---

### S9 — Relationship map

| | |
|--|--|
| **Problema WorkOS** | Litere↔panou / joints / mounts trebuie vizibile când există date; azi `element_bindings` deseori gol. |
| **Pattern căutat** | Lightweight relationship map / link list (from→to), optional mini graph — nu full graph DB UI. |
| **Criterii de acceptare** | Empty state onest („relație neconfirmată”); tipuri: mounts_on / joint / interfaces_panel; click selectează endpoints. |
| **Risc design system paralel** | Mediu — node-graph demos atrag complexitate. |
| **Adaptat la WorkOS** | Doar din Product Truth / `element_bindings` / joints; zero invenție UI. |
| **Nu copia din demo** | Infinite canvas mind-map; neo4j explorer; auto-layout care mută geometry. |

**Search hints:** `entity relationship list`, `simple connection map ui`, `link inspector from-to`.

---

### S10 — Sticky action bar

| | |
|--|--|
| **Problema WorkOS** | Confirm composition / confirm segmented / continue workflow se pierd sub form lung. |
| **Pattern căutat** | Sticky bottom (or top) action bar: primary/secondary/destructive + context summary. |
| **Criterii de acceptare** | Acțiuni gated pe validation; summary scurt (ex. „Panou PROPOSED — 2 segmente”); nu duplicate AppShell topbar. |
| **Risc design system paralel** | Scăzut–mediu. |
| **Adaptat la WorkOS** | Footer Intake V6 existent — densifica; acțiuni reale, nu stub marketing. |
| **Nu copia din demo** | Floating glass dock; emoji actions; multi-step wizard progress ca produs nou. |

**Search hints:** `sticky form action bar`, `bottom toolbar save cancel`, `composer footer actions`.

---

### S11 — Dense technical form

| | |
|--|--|
| **Problema WorkOS** | Câmpuri ACM (thickness, depth, fold, frame, finish) trebuie dense și tehnice pe dark, nu „settings SaaS”. |
| **Pattern căutat** | Compact labeled fields grid: mm units, grouped sections, inline help, unit suffixes. |
| **Criterii de acceptare** | Unități vizibile; groups Structură / Finisaj / Prindere; empty ≠ silent default; compatible cu inspector. |
| **Risc design system paralel** | Mediu — white form layouts din 21st. |
| **Adaptat la WorkOS** | Mapare la `mounting_solution` / casing / face treatments; dark cards; RO labels din terminology registry. |
| **Nu copia din demo** | Soft onboarding copy; illustrative icons pe fiecare field; light gray panels. |

**Search hints:** `dense technical settings form`, `engineering parameters form`, `compact unit input grid`.

---

### S12 — Side-by-side configuration + preview

| | |
|--|--|
| **Problema WorkOS** | Operatorul configurează și trebuie să vadă ansamblul simultan (composition + geometry/blueprint). |
| **Pattern căutat** | Split view: left config (list+inspector/form), right preview/schematic; responsive stack. |
| **Criterii de acceptare** | Selection sync bidirectional; rail validation nu rupe split; full-width util (nu max-w marketing). |
| **Risc design system paralel** | Ridicat — demos „AI studio” / white canvas. |
| **Adaptat la WorkOS** | În AppShell; dark both panes; preview consumă truth, nu mock SVG. |
| **Nu copia din demo** | Chat-first layout; prompt box; stock hero image; unrelated KPI column. |

**Search hints:** `split view editor preview`, `configurator with live preview`, `form canvas dual pane`.

---

## 3. Matrice de prioritizare pentru auditul următor

| ID | Pattern | Prioritate căutare | Depinde de domain gap? |
|----|---------|--------------------|------------------------|
| S1 | Modular components | P0 | Parțial — UI poate arăta sibling chiar înainte de fix CFG, cu status missing |
| S2 | Expandable rows | P0 | Nu |
| S8 | Detected/proposed/confirmed | P0 | Nu (unifică badges) |
| S7 | Validation rail | P0 | Beneficiază de coduri CFG din audit |
| S12 | Side-by-side | P1 | Preview real după geom readiness |
| S4 | Geometry preview | P1 | CCC există; layer xy slab |
| S5 | Blueprint schematic | P1 | Read model încă neimplementat — UI doar mock-wire pe contract |
| S3 | Component inspector | P1 | Mounting fields deseori absente |
| S6 | Layer list | P1 | Deja parțial în Straturi — refine |
| S11 | Dense technical form | P2 | După instanțiere SUPPORT/mounting |
| S9 | Relationship map | P2 | După `element_bindings` populate |
| S10 | Sticky action bar | P1 | Refine footer existent |

---

## 4. Reguli de evaluare în `WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_AUDIT`

Când se rulează auditul următor, pentru **fiecare** hit 21st.dev:

1. Notează **URL / component name**.
2. Mapează la **S1–S12** (un primary, optional secondary).
3. Scor: *operator fit* / *WorkOS dark fit* / *domain safety* / *parallel-system risk*.
4. Decizie doar: **CANDIDATE_ADAPT** | **REJECT** | **DEFER** — **nu** „implementă”.
5. Dacă patternul forțează un al doilea shell, white operational cards, sau inventă ownership → **REJECT**.
6. Dacă patternul atrage Nivel 2/3 manufacturing → **REJECT** pentru acest pas (reține doar pe listă „viitor manufacturing UI”, out of scope).

**Out of scope explicit pentru acel audit:**

- nesting CNC, CUT/FOLD, DXF, LED auto, manufacturing package;
- rescriere Product Truth / remediation writes;
- port fidel sketch take 1;
- GO implementare UI.

---

## 5. Deliverable așteptat din auditul următor

Un singur raport `WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_AUDIT` care conține:

1. Tabel S1–S12 × candidați 21st (0–N per zonă).
2. Shortlist adaptare pe dark WorkOS (max ~8 patternuri).
3. Explicit: ce rămâne blocked până la fix CFG instanțiere ACM.
4. Handoff către implementare UI **doar dacă** owner dă GO separat.

---

## 6. Pointer înapoi la domain

Contractul minim blueprint și ownership matrix rămân în auditul de configurare (§5–§6).  
21st.dev **nu** modifică:

- `SUPPORT_CONTOUR` ca identitate panou;
- nested `segmented_background.panels[]`;
- letters ownership EXTERNAL;
- Nivel 1 vs 2 vs 3 feasibility.

---

## Owner gate

Handoff livrat. **STOP** — așteaptă GO pentru `WORKOS_UI_SYSTEM_21ST_BLUEPRINT_INTEGRATION_AUDIT` (căutări 21st + evaluare).  
Fără implementare, fără selecție design final, fără remediation.
