# Intake V6 — Status Semantics Normalization Audit

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline HEAD:** `30335bb`  
**Mode:** Read-only — **no implementation**  
**Runtime evidence:** FE `:3001` · BE `:8003` (compat PASS) + screenshots from accepted live packs on this branch

Research: compound tracks reconciled with code search (`intakeV6OperatorVocabulary`, badges, blockers, Finisaje OK/Lipsă, segmented/electrical enums).

---

## 1. Verdict

**PASS (audit).**  
UI foundation is frozen and coherent. Remaining trust risk is **status vocabulary drift**: the same business meaning uses different words (`OK` vs `Confirmat`, `Propus` vs `Propunere`, `De confirmat` vs `Propunere`), and the same word (`OK`, `Lipsă`, `Confirmat`) means different things in different tabs.

**No critical architectural gap.**  
**Do not implement until owner ranks the canonical set below.**

---

## 2. Current status inventory (summary)

| Family | Visible words (primary) | Main surfaces |
|--------|-------------------------|---------------|
| Proposal | Propunere, Propus, Sugerat, Inclus în propunere | Page 1 roles, Montaj cluster/panel, composition |
| Needs operator | Confirmare necesară, Necesită confirmare, De confirmat, Draft / neconfirmat, Neconfirmat | Page 1, composition, electrical, Confirmare |
| Missing data | Lipsă, Lipsă date (geom), culoare lipsă, Lipsește | Finisaje cards, summaries, header |
| Confirmed | Confirmat, Confirmată, OK, Complet, Ansamblu confirmat | Page 1, Finisaje, Montaj, composition, Confirmare |
| Ready | Pregătit, Totul OK, Date tehnice pregătite… | Confirmare / header |
| Warning | Avertizare, Atenție, observații analiză, Necesită verificare tehnică | banners, footer, guards |
| Blocker | Blocant, Blocat, Blocată, Blocaj, Probleme | sticky, composition, Confirmare |
| Owner | Necesită confirmarea administratorului, Decizie admin (vocab tone) | ACP modules, readiness |
| Domain config (not severity) | 220V direct…, Alimentare din alt panou, Fără 220V local, LED activ/oprit | electrical / lighting selects |

Existing helper (partial): `frontend/src/lib/intakeV6/intakeV6OperatorVocabulary.ts` — readiness + severity tones; **not** used by Finisaje `OK`/`Lipsă` or Page 1 pending split.

---

## 3. Status matrix (important rows)

| Current text | Location | Internal state | Real meaning | Problem | Recommended semantic |
|--------------|----------|----------------|--------------|---------|----------------------|
| Propunere | Page 1 role table | `pending` / unset confirmation | Analyzer suggestion not accepted | OK as proposal | **Propunere** |
| De confirmat | Page 1 status icon aria | same `pending` | Same as above | **Different word, same state** | **Propunere** *or* **Necesită confirmare** (pick one) |
| Confirmare necesară | Page 1 operator panel badge | roles incomplete | Operator must finish roles | Soft panel status | **Necesită confirmare** |
| Confirmat | Page 1 role / binding | `confirmed` / `CONFIRMED` | Accepted authority | OK | **Confirmat** |
| OK | Finisaje letter/artwork card | `group.confirmed` / `row.confirmed` | Finish confirmed | Looks like “all good / ready”, English | **Confirmat** |
| Lipsă | Finisaje card | missing color or unconfirmed artwork | Missing required field *or* not confirmed | Overloaded | **Lipsă date** vs **Necesită confirmare** |
| Confirmat in Pasul 1 | Artwork Finisaje | step-one role confirmed, finish open | Role done; finish open | Green “ok” tone misleading | **Necesită confirmare** (finish) |
| Necesită confirmare | Composition badge | composition not confirmed | Must confirm composition | OK | **Necesită confirmare** |
| Confirmată | Composition | composition confirmed | Accepted | Gendered variant OK | **Confirmat** |
| Blocată | Composition | blockers / blocked | Cannot confirm composition | OK family | **Blocant** |
| Propunere | Montaj cluster shell | segmented `PROPOSED` | Segmented proposal | OK | **Propunere** |
| Propus | Segmented panel badge | same `PROPOSED` | Same | **Propus ≠ Propunere** | **Propunere** |
| Confirmat | Segmented / electrical | `CONFIRMED` | Accepted assembly/electrical | OK | **Confirmat** |
| Draft / neconfirmat | Electrical panel badge | status ≠ CONFIRMED | Electrical not confirmed | Mixed EN/RO | **Necesită confirmare** |
| Neconfirmat | Electrical supply select | `UNCONFIRMED` | Supply mode not chosen | Config value, not severity badge | Keep as option label; badge = **Necesită confirmare** |
| 220V direct pe panou | Electrical select | `DIRECT_220V` | Config choice | Not a severity | Keep domain label |
| Necesită confirmarea administratorului | ACP readiness | `OWNER_GATE_REQUIRED` | Admin/owner must decide | Must not look like crash | **Decizie admin** |
| Necesită verificare tehnică | Page 1 Guarded | bindable.guards | Soft technical constraint | Not a blocker | **Avertizare** |
| Blocat / Atenție / Pregătit | Confirmare consolidated | tiers | Confirm readiness | Close to canonical | Align wording only |
| Totul OK | Header aggregate | all green | Workspace ready strip | English OK overload | **Pregătit** |
| Probleme și avertizări — N | Footer | mixed severities | Mixed drawer | Hides Blocant vs Avertizare | Split counts |
| Blocaj tehnic: CODE | Blocker banner fallback | unmapped code | Looks like system failure | May be owner/config | Map via vocabulary; never raw for owner gates |
| manual_review / impossible | Lighting PSU line | `psu_allocation_status` | Engine state | Raw English leak | Map to **Avertizare** / **Blocant** |

Full track detail: research agent inventory (files cited above).

---

## 4. Conflicts found

### Same meaning → different words
1. Pending layer role: **Propunere** vs **De confirmat** vs **Confirmare necesară**
2. Segmented proposal: **Propunere** (cluster) vs **Propus** (panel) vs vocab **Propunere segmentare**
3. Confirmed finish: **OK** vs **Confirmat** / **Confirmată**
4. Needs check: **Necesită confirmare** / **verificare** / **reconfirmare** / **Atenție** / **De completat**

### Same word → different meanings
1. **OK** — finish confirmed; SVG ready; pricing ok; header “Totul OK”
2. **Lipsă** — missing color; artwork unconfirmed; geometry missing; header field empty
3. **Confirmat** — role, binding, segmented, electrical, composition, and “Confirmat in Pasul 1” (finish still open)
4. **Propunere** — analyzer suggestion; segmented proposal; composition membership; binding suggested

### Warning vs blocker
- Sticky mixes **Blocaj** / **Avertisment**; footer lumps “Probleme și avertizări”
- Segmented `PROPOSED` often sticky **warning** while looking like a hard Montaj gate
- Composition lists blockers + warnings in one amber block

### Proposal vs confirmed
- Finisaje silent when unconfirmed but colors present (no badge)
- Artwork “Confirmat in Pasul 1” uses success tone

### Owner vs technical error
- Primary ACP lines map owner gates to RO (good)
- Unmapped codes → `Blocaj tehnic:` can look like system failure
- Raw `OWNER_GATE_*` still in technical accordions (acceptable if collapsed)

---

## 5. Canonical semantic proposal (small set)

| # | Semantic ID | Primary RO label | Meaning | Blocks continue? |
|---|-------------|------------------|---------|------------------|
| 1 | `proposal` | **Propunere** | System suggestion not accepted | No (unless product rule says soft-gate) |
| 2 | `needs_operator` | **Necesită confirmare** | Operator must confirm/complete | Often yes for that gate |
| 3 | `missing_data` | **Lipsă date** | Required value absent | Usually yes for that field |
| 4 | `warning` | **Avertizare** | Attention; not sole hard stop | No |
| 5 | `blocker` | **Blocant** | Cannot continue / confirm | Yes |
| 6 | `owner_decision` | **Decizie admin** | Owner/admin must decide | Yes for gated domain |
| 7 | `confirmed` | **Confirmat** | Authority accepted | — |
| 8 | `ready` | **Pregătit** | Ready for next step (≠ Confirmat) | — |

**Domain config labels** (220V modes, LED on/off) stay as nouns — not severity badges.

**Ban in primary UI:** `OK`, English `Ready`/`Warning`, raw `OWNER_GATE_*`, raw `manual_review`.

---

## 6. Recommended mapping (implementation later — not now)

| Current | → Canonical |
|---------|-------------|
| OK (Finisaje) | Confirmat |
| Lipsă (color missing) | Lipsă date |
| Lipsă (unconfirmed finish) | Necesită confirmare |
| De confirmat (icon) | Align with Propunere *or* Necesită confirmare (owner pick) |
| Propus (segmented panel) | Propunere |
| Draft / neconfirmat | Necesită confirmare |
| UNCONFIRMED (as badge) | Necesită confirmare |
| UNCONFIRMED (as select option) | keep “Neconfirmat” |
| Totul OK | Pregătit |
| Confirmată / Complet (when meaning = accepted) | Confirmat |
| OWNER_GATE_REQUIRED | Decizie admin |
| Guarded | Avertizare |

Route all new/changed labels through `intakeV6OperatorVocabulary` (+ optional `operatorStatusSemanticRo(semanticId)`).

---

## 7. Locations affected (if GO later)

| Area | Files (examples) | Priority |
|------|------------------|----------|
| Finisaje badges | `IntakeV6ReviewLetterGroupsSection.tsx`, `IntakeV6ArtworkFinishSection.tsx` | P0 |
| Page 1 pending wording | `IntakeV6LayersRoleTable.tsx`, `IntakeV6LayerStatusIcon.tsx`, `IntakeV6LayersOperatorPanel.tsx` | P0 |
| Segmented Propunere/Propus | `segmentedBackground.ts` `statusLabelRo`, `IntakeV6ReviewStep` cluster shell | P1 |
| Electrical badge | `IntakeV6SegmentedElectricalPanel.tsx` | P1 |
| Sticky/footer split | blocker banner display, footer issue groups | P1 |
| Confirmare / header | consolidated status, review header status | P2 |
| Lighting PSU raw | `IntakeV6ReviewLightingSection.tsx` | P2 |

**Do not touch:** analyzer, PD, Aggregate, segmented/electrical **contracts**, Montaj IA structure, Page 1 flow, composition IA.

---

## 8. Segmented background status audit

| Internal | UI today | Operator meaning | Issue |
|----------|----------|------------------|-------|
| PROPOSED | Propunere / Propus | Proposal to confirm | Dual wording |
| CONFIRMED | Confirmat / Ansamblu confirmat | Accepted | OK |
| REJECTED | Respins | Explicit reject | OK |
| INACTIVE / none | Inactiv / Fără segmentare | Not in play | OK |
| Cutout/insert blockers | RO blocker messages | Hard stop | Severity = Blocant (good) |
| Crossing allowed / distributed graphic | informational copy | Soft info | Keep Informativ |

Contracts unchanged. Wording only if GO.

---

## 9. Electrical status audit

| Internal | UI today | Recommended meaning |
|----------|----------|---------------------|
| DIRECT_220V | 220V direct pe panou | Config choice — keep |
| SHARED_FROM_PANEL | Alimentare din alt panou | Config choice — keep |
| NO_LOCAL_220V | Fără 220V local | Config choice — keep |
| UNCONFIRMED | Neconfirmat (option) + contributes to Draft badge | **Not configured yet** — operator must choose; not “impossible”, not “error” |
| Assembly CONFIRMED | Confirmat | Confirmat |
| Assembly else | Draft / neconfirmat | Necesită confirmare |

---

## 10. Owner gate audit

| Pattern | Today | Assessment |
|---------|-------|------------|
| ACP LED/PSU `OWNER_GATE_REQUIRED` | RO “Necesită confirmarea administratorului” in primary | Good — not red error |
| Gate lists “nu sunt valori implicite” | Explains who decides | Good |
| Raw in advanced accordion | Collapsed | Acceptable |
| Unmapped → Blocaj tehnic | Can look like crash | Risk — map owner codes before fallback |

Owner gates must remain **Decizie admin**, never **Blocant** styling alone without explanation.

---

## 11. Accessibility audit

| Pattern | Color-only? | Text / aria | Notes |
|---------|-------------|--------------|-------|
| Page 1 status icons | Icon + aria Confirmat/De confirmat | Yes | Align wording with table |
| Finisaje OK/Lipsă | Badge text + tone | Partial | Text OK; tone reuse weak |
| Sticky blocker | Title + list + severity prefix | Good | Keep text severity |
| Footer Continuă disabled | `aria-describedby` reason (post clarity) | Good | Preserve |
| Composition toggle | `aria-expanded` | Good | Preserve |
| Electrical selects | Native options | Good | Keep domain nouns |

Recommendation later: one semantic → one badge tone + always include text label (never color alone).

---

## 12. Screenshot index

Evidence from accepted live packs on this branch (same FE/BE stack). Paths under `screenshots/`.

| # | File | State illustrated |
|---|------|-------------------|
| 1 | `01_page1_confirmed.png` | Page 1 confirmed / ready path |
| 2 | `02_page1_pending.png` | Page 1 pending handoff |
| 3 | `03_finisaje_ok_lipsa.png` | Finisaje OK / Lipsă badges |
| 4 | `04_montaj_structure.png` | Montaj IA (status chrome present) |
| 5 | `05_segmented_proposed.png` | Segmented PROPOSED |
| 6 | `06_segmented_confirmed.png` | Segmented CONFIRMED |
| 7 | `07_sticky_blocker.png` | Sticky final blocker |

Gaps (documented, not blocking audit): dedicated owner-gate-only and “final ready” frames — available in segmented/vocab packs; no new code written to capture them.

---

## 13. Figma audit

| Item | Finding |
|------|---------|
| Runtime vs Figma statuses | Figma structural checkpoints (Page 1 / Page 2) predate status unification |
| Colors | Design may imply “green = done” for OK — matches Finisaje risk |
| Tokens | No single Figma status token set for Intake V6 operator semantics |
| Action | **Do not update Figma** until owner accepts canonical set |

Runtime remains acceptance truth.

---

## 14. Risks

1. Renaming OK→Confirmat without tests breaks screenshot/E2E string asserts.
2. Merging Propunere with Necesită confirmare loses analyzer-vs-operator distinction.
3. Treating UNCONFIRMED as error scares operators.
4. Touching Montaj copy may reopen frozen IA if not strictly badge-only.
5. Over-expanding vocabulary beyond 8 states recreates drift.

---

## 15. What must remain frozen

- Page 1 IA / handoff structure  
- Composition demotion / sticky blocker architecture  
- Montaj Fundal / comercial / Avansat / segmented / 220V **structure**  
- Analyzer, PD, Aggregate, contracts, pricing, Execution  
- Display-label helper truth boundary  

This audit does **not** reopen those.

---

## 16. Owner decisions required before implementation

1. Pending layer: **Propunere** (analyzer) vs **Necesită confirmare** (action) — one primary label?  
2. Finisaje: confirm **OK → Confirmat** and split **Lipsă** meanings?  
3. Segmented: force **Propunere** everywhere (drop Propus)?  
4. Electrical badge: **Draft / neconfirmat → Necesită confirmare**?  
5. Scope of next build: Finisaje+Page1 only, or include Montaj badges (structure frozen)?

---

## 17. Implementation recommendation (after GO only)

**Single coherent build:**  
`refactor(intake-v6): normalize status semantics`

1. Add `operatorStatusSemanticRo` (+ tones) on existing vocabulary layer.  
2. Replace Finisaje OK/Lipsă + Page 1 pending split.  
3. Align segmented Propunere/Propus + electrical Draft badge.  
4. Split sticky/footer Blocant vs Avertizare counts (no IA redesign).  
5. Targeted Vitest + live screenshots; Montaj structure tests must stay green.  

**No Montaj layout changes. No contract changes.**

---

## 18. Cat sunt in directia stabilita

**Cat sunt in directia stabilita: 99/100%**

(Status trust cleanup is the last vocabulary seam before polish.)
