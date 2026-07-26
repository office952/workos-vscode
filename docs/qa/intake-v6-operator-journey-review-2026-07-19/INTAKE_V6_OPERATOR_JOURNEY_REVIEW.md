# Intake V6 — Operator Journey Review Audit

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline HEAD:** `b680956`  
**Mode:** Read-only — **no implementation**  
**Persona:** Operator producție publicitară — cunoaște litere/casete/finisaje/LED/montaj; **nu** cunoaște ProductDefinition, Aggregate, contracts, template codes.

**Runtime:** FE `http://127.0.0.1:3001` · BE `http://127.0.0.1:8003` · compat capabilities PASS  
**Workspace:** `c9ef796a-2731-418e-8a19-2b35f1461f61` (`IV6-15CCCD91`)  
**Fixture:** `C:/Users/offic/Desktop/fisiere-teste-svg/litere-cu-fundal-acm-segmentat.svg`  
**Evidence:** `screenshots/` + `runtime/observations.json`

---

## 1. Verdict

**PARTIAL — foundation curată, journey încă grea pentru operator nou.**

Componentele individuale (Page 1 labels, Finisaje, status semantics, Montaj IA) sunt vizibil mai bune decât auditul UI/UX din `7f3e507`.  
Ca **experiență de la A la Z**, operatorul nou încă:

- vede **prea multe canale de avertizare** simultan;
- întâlnește **limbaj tehnic** (TPL-…, FinishSetup, analyzer, legacy/deprecated) pe nivelul principal;
- pierde firul: *ce fac acum* vs *de ce Continuă e blocat*;
- ajunge la Confirmare cu **decizii lipsă** și mesaje care încă cer compoziție.

Nu e un eșec de arhitectură UI. E un **gol de coaching / ordine informațională / un singur fir de acțiune**.

---

## 2. Operator persona (applied)

| Știe | Nu știe |
|------|---------|
| Litere volumetrice, ACM/casete, Oracal/RAL, LED, montaj pe site | Product System codes, FinishSetup, Aggregate, „authority live”, contract English |

Evaluarea judecă: *ar găsi următorul gest fără să deschidă acordioane tehnice?*

---

## 3. Runtime environment

| Item | Value |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `b680956` |
| Foreign WIP | Present — untouched |
| FE / BE | `:3001` / `:8003` 200 |
| Compat | `intake_v6.workspaces` + local-compat capabilities present |
| Route | `/intake-v6/:id/operator` |
| Steps | Straturi → Configurare → Confirmare |
| Tabs | Finisaje · Iluminare și surse · Montaj |
| Reload shot | Not captured (walk timeout after Confirmare) — Persist proven in prior segmented packs |

---

## 4. Full journey map

```text
Start (empty workspace)
  |  upload SVG (CTA ×3: card / panou / footer)
  v
Analiză + preview
  |  decide roles (Element N)  ←── friction: Contur suport hint vs Confirmă toate
  |  optional: Compoziție confirm   ←── often deferred / easy to miss
  v
Continuă la Configurare
  |
  +--> Finisaje (Față/Cant/Spate)  ←── top: composition gate + TPL + red blocker count
  +--> Iluminare (LED/PSU)         ←── good LED≠220V copy; same sticky gate above
  +--> Montaj
         |  Fundal și carcasă
         |  Segmentare Propunere → Confirmă/Respinge
         |  220V (only after segmented confirm)  ←── invisible until then
         |  Comercial (demoted — good)
  v
Continuă la Confirmare  (often DISABLED; progress nav can still open Confirmare)
  |  Scope + „decizii lipsă” + analyzer prompt
  v
Continuă către ofertă / draft  ←── trust risk if CTA looks ready while incomplete
```

**Smooth:** 3-step chrome; Element labels; Finisaje Față·Cant·Spate; Iluminare vs 220V wording; Montaj order strip; Segmented Confirmă/Respinge.  
**Friction:** multi-banner warnings; composition sticky; template codes; Continuă disabled without a single clear checklist; Confirmare reachable while unfinished.  
**Dead-end feel:** Electrical panel absent until segmented confirmed — correct technically, unexplained for first-time user.

---

## 5. Step-by-step observations

### Start
1. **Must do:** upload SVG.  
2. **Next step:** obvious (Încarcă SVG) but **repeated 3×**.  
3. **Too much text?** Mild — „Ce producem?” before file is fine.  
4. **Technical?** Low.  
5–7. Info present; finds upload quickly.  
8–11. Clear decision; status soft; Continuă disabled with footer reason — good.

### Page 1 after analysis
1. Confirm roles for Element 1/2.  
2. Primary CTA „Confirmă toate sugestiile” is clear.  
3–4. Instruction about Contur suport + orange **FinishSetup** failure = cognitive spike.  
5. Needed info (roles) present; save-error competes.  
6–7. Operator looks for „care e fundalul?” — hint helps, Confirm all may confirm wrong roles.  
8–11. Status „Necesită confirmare” good; trust damaged by FinishSetup string.

### Page 1 after confirm
1. Expect Continuă.  
2. Yes — Continuă enabled; handoff summary good.  
3–4. Still „Probleme și avertizări — 3” unexplained.  
5. Composition still „Necesită confirmare” below fold risk.  
8–11. Roles Confirmat clear; assembly truth still incomplete.

### Finisaje
1. Thinks: set Față/Cant.  
2. Actually blocked by **composition** + sticky red „blocată de N elemente”.  
3–4. TPL / legacy / English modular-form line = **internal mechanics**.  
5. Finish controls exist but below/around gates.  
6–7. Operator searches „de ce nu pot continua?” — finds composition button, not finish gap list.  
8–11. Finish status „Necesită confirmare” OK; trust mixed with pricing sidebar „tarif lipsă”.

### Iluminare
1. Choose LED type / PSU.  
2. Controls clear; calculated modules/W helpful.  
3–4. Same sticky composition/blocker above tab work.  
5–11. LED≠carcasă 220V message = **trust win**. Pricing noise continues.

### Montaj / Fundal / Segmentare
1. Confirm multi-panel proposal.  
2. Confirmă/Respinge clear.  
3–4. `contour=…` / `TPL-ACM-…` still visible.  
5. Electrical not shown yet — operator may think „unde e 220V?”  
8–11. Propunere badge good; commercial demoted good.

### Confirmare
1. Final check before offer.  
2. Ambiguous: „3 decizii lipsă” + „Confirmă compoziția…analyzer” + Continuă către ofertă.  
3–4. Analyzer language.  
8–11. Progress shows Configurare ✓ while unfinished work remains — **false completion**.

---

## 6. Cognitive load findings

| Pattern | Severity |
|---------|----------|
| 3+ simultaneous warning surfaces (global system status, sticky blocker, footer problems, composition badge) | **High** |
| Decision density on Configurare first viewport (composition + scope + blocker + tabs) | **High** |
| Pricing sidebar during product decisions | **Medium** |
| Expandables required to understand blockers („Vezi detalii tehnice”) | **Medium** |
| Must remember Page 1 Contur suport instruction on Montaj | **Medium** |
| Confirmă toate may conflict with Contur suport guidance | **High** |

---

## 7. Information order findings

| Info | Today | Should be |
|------|-------|-----------|
| Composition confirm | Sticky top of Configurare + footer | **Before** Finisaje work, or one modal gate — not parallel |
| TPL / legacy codes | Primary composition card | **Only on request** (Detalii tehnice) |
| FinishSetup / save errors | Orange primary banner | Operator RO + action; raw token collapsed |
| Blocker count „N elemente” | Red card without ranked actions | **During** decision: ordered checklist |
| Live pricing / tarif lipsă | Always-on right rail | **After** product truth / on Confirmare |
| 220V panel | Hidden until segmented confirm | Informational „apare după Confirmă segmentarea” |
| Segmented Confirma/Respinge | During Montaj — correct | Keep |

---

## 8. Visual trust findings

**Communicates product understanding when:** Element N labels, preview thumbnail, LED module count, segmented panel list, Față/Cant/Spate cards, status semantics (Propunere / Necesită confirmare / Confirmat).

**Leaks internal mechanics when:** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`, `FinishSetup`, `authority live`, `legacy/deprecated`, English „Full-product composition from modular form contract”, `contour=hash`, global „Stare sistem: necesită verificare” unrelated to job.

Verdict: **mixed** — product language improved; Configurare top strip still feels like an engineering console.

---

## 9–12. Area findings (summary)

### Page 1
- Detected elements readable (Element + color). Preview helps.  
- Roles clear enough; Contur suport coaching vs Confirm all is the main trap.  
- Hover/inspect not re-tested this pass; prior packs say legend helps.

### Finisaje
- Față/Cant/Spate understandable. Ownership demoted (good).  
- Operator cannot focus finishes while composition + red blocker dominate.

### Iluminare
- Choose / calculated result / source separation mostly clear.  
- Competes with composition gate and cost rail.

### Montaj
- Physical assembly path clearer than pre-IA audits.  
- Segmentation understandable. Electrical preparation **gated** without explainer. Commercial demoted correctly.

---

## 13. Hidden experience problems

1. Continuă disabled — reason split across footer / red card / composition (not one list).  
2. Status technically correct, emotionally confusing (Configurare ✓ on Confirmare while 3 decisions missing).  
3. Warning (FinishSetup) before operator has context.  
4. Same ask repeated: confirm composition (card, footer, Confirmare banner).  
5. 220V missing when needed → must guess Montaj order.  
6. Heavy scroll on Montaj.  
7. Operator opens „Detalii tehnice” because primary copy is opaque.  
8. Save / sync states („Sincronizare automata…”, „Salvează…”) compete with Continue.  
9. Calculated LED shown — good; commercial price „nu este disponibil” undermines confidence.  
10. Human confirmation needed for composition — clear button, but timing wrong.

---

## 14. Severity ranking (experience)

| Sev | Finding |
|-----|---------|
| **P0** | Configurare first viewport = composition gate + TPL/legacy + red blocker count before tab work |
| **P0** | Multiple concurrent warning channels (global / sticky / footer / card) |
| **P1** | Contur suport coaching vs „Confirmă toate sugestiile” |
| **P1** | Technical / English strings on primary surfaces |
| **P1** | Confirmare reachable / looks progressed while unfinished |
| **P2** | Pricing rail during configuration |
| **P2** | 220V invisibility without explainer |
| **P2** | Global „Stare sistem: necesită verificare” noise |

---

## 15. What is already good

- Frozen 3-step + 3-tab IA matches operator mental model.  
- Display labels + status semantics reduce vocabulary chaos.  
- Page 1 Element naming + handoff summary.  
- Finisaje card model (Față · Cant · Spate).  
- Explicit LED vs carcasă 220V copy.  
- Montaj „ordine de lucru” + commercial demotion.  
- Segmented Propunere with Confirmă/Respinge.  
- Footer often explains Continuă when empty/start.

---

## 16. What remains frozen

Page 1 structure · composition architecture · Finisaje structure · Iluminare · Montaj IA · segmented/electrical contracts · status vocabulary · analyzer · PD/Aggregate · backend/schemas.

This audit does **not** reopen them for redesign.

---

## 17. Recommended future builds (direction only — no GO)

1. **Operator action spine** — one ranked checklist for Continuă; demote multi-banner noise.  
2. **Composition timing** — confirm composition as a clear gate *before* Finisaje work, without TPL in primary.  
3. **Confirmare honesty** — step checks / CTA state match unfinished decisions.  
4. **First-run coaching** — Contur suport vs Confirm all; „220V apare după confirmarea segmentării”.

Do **not** start with new components or Montaj redesign.

---

## 18. Owner decisions

1. Accept PARTIAL journey verdict and freeze until GO on one spine build?  
2. Priority: composition timing vs blocker checklist vs technical demotion?  
3. Is Confirmare navigation allowed while Continuă disabled (current), or hard-block?  
4. Should pricing rail hide until Confirmare?  
5. Scope of next build: copy/order only, or light IA tweak without Montaj reopen?

---

## Screenshot index

| # | File | Step |
|---|------|------|
| 1 | `01_start_empty.png` | Start |
| 2 | `02_page1_after_analysis.png` | Page 1 analyzed |
| 3 | `03_page1_roles_confirmed.png` | Page 1 roles |
| 4 | `04_finisaje.png` | Finisaje |
| 5 | `05_iluminare.png` | Iluminare |
| 6 | `06_montaj_top.png` | Montaj top |
| 7 | `07_fundal_carcasa.png` | Fundal |
| 8 | `08_segmented_state.png` | Segmentare |
| 9 | `09_electrical_state.png` | Electrical (not yet visible) |
| 10 | `10_before_confirm_transition.png` | Pre-confirm blocked |
| 11 | `11_confirmare.png` | Confirmare |
| — | `supp_*.png` | Prior-pack supplements |

Full text excerpts: `runtime/observations.json`.

---

## Cat sunt in directia stabilita

**Cat sunt in directia stabilita: 92/100%**

(UI foundation done; journey coaching / information order is the remaining trust gap.)
