# BUILD: Intake-to-Quote Process Automation Audit

**Date:** 2026-06-07  
**HEAD:** `841cc96`  
**Type:** Documentation-only audit (no runtime changes)

---

## Pre-flight

| Item | Value |
|------|-------|
| Branch | `master` |
| HEAD | `841cc96` |
| Git status (start) | clean |
| Backend :8000 | healthy |
| Frontend :3000 | up |
| Counts before | intakes **22**, quotes **7**, orders **8** |
| Counts after | **unchanged** (no data mutations) |

---

## Browser routes tested

| Route | Intake / flow | Result |
|-------|---------------|--------|
| `/intake` | List + Cerere Nouă available | PASS |
| `/intake/IR-MQ3C869E` | Volumetric modular workspace (`data-testid=volumetric-intake-page`) | PASS |
| `/intake/IR-MQ3JV8GD` | Volumetric + vector pathway (Vodafone) | PASS |
| `/intake/IR-MQ3E7K2V` | Generic unresolved — terrain + CUI + assignee before work type | **FINDING** |
| `/intake/WI-SMOKE-P001` | Smoke baseline intake (metadata confirmed via API) | PASS (reference) |
| `/quotes` | Quotes list (navigation verified) | PASS |

Video reference (operator recording 2026-06-07): `IR-MQ3JV8GD` vector pick — filename empty due to save race (fixed in `841cc96`).

---

## Key findings (operator impact)

### 1. Too early / illogical panels (generic unresolved)

On `IR-MQ3E7K2V` (`product_family` empty):

- Full **Audit teren** (address, photos, power) visible while work type not chosen
- **CUI / Interogare fiscală** visible before product context
- **Confirmă template** / **Mergi la teren** action links active prematurely
- Readiness blockers reference template/spec/dimensions not yet applicable

**Recommendation:** BUILD-INTAKE-GATE-CONDITIONAL (P0)

### 2. Duplicate inputs

- `delivery_type` — Quick Start + side panel
- Vector file + layer mapping — fast ask + Vector Studio §9
- Quote missing lists — side panel, quote tab, optional §10 prep panel

**Recommendation:** BUILD-DELIVERY-SYNC + BUILD-VECTOR-SINGLE-SURFACE (P0–P1)

### 3. Vector path still manual for quote geometry

SVG provides layers/metadata but **not** simulate-ready area/perimeter/count (by design — no reliable parser). Operator must enter §3 geometry manually after fast ask. This is correct but feels like “extra step” — needs clearer **review** UX, not hidden requirement.

**Recommendation:** BUILD-READINESS-STAGES + BUILD-VECTOR-REVIEW-NOT-REENTER (P1)

### 4. Production fields mixed into intake

§1 text/font/notes, vinyl roll details, CNC flags — needed for **final quote / production**, not preliminary simulate. Should be conditional or collapsed on vector path.

**Recommendation:** BUILD-CONDITIONAL-FINISH (P2)

### 5. Automation safe today (high confidence)

- File metadata + layer detection from SVG
- Pathway persistence
- Delivery sync from Quick Start
- Template auto-confirm when volumetric selected at Quick Start
- Depth default 60mm, conditional Oracal/RAL fields
- Assignee prefill from session

### 6. Automation NOT safe today

- letter_face_area_m2 / letter_perimeter_m / letter_count from SVG — **none** until validated parser
- Do not relax CostEngine or WI-SMOKE-P001 baseline

---

## Journey table (condensed)

| step | problem | automation opportunity |
|------|---------|------------------------|
| Quick Start delivery | re-asked in workspace | auto-sync |
| Template confirm | extra click after volumetric Quick Start | auto-confirm optional |
| Vector SVG pick | was losing filename (race) | fixed 841cc96 |
| Fast ask → 8 sections | feels like second form | review-oriented UI |
| §3 geometry | manual entry required | LED/PSU suggest only |
| Generic unresolved terrain | shown too early | conditional on install + resolved |
| Quotes Ofertă nouă | separate wizard | keep (correct) |

---

## Recommended next build

**BUILD-INTAKE-GATE-CONDITIONAL**

- Hide terrain, fiscal, template CTAs on unresolved intakes
- Stage readiness blockers (ops vs simulate vs final quote)
- No pricing/CostEngine changes
- Browser PASS: `IR-MQ3E7K2V` shows only work-type CTA + client/assignee/delivery

---

## Confirmations

- [x] No pricing changes
- [x] No CostEngine changes
- [x] No quote/order created
- [x] No Reference Catalogs started
- [x] No fake geometry calculated
- [x] WI-SMOKE-P001 baseline not affected (no code changes)
- [x] No runtime changes in this audit

---

## Artifacts

- Architecture audit: `docs/architecture/INTAKE_TO_QUOTE_PROCESS_AUTOMATION_AUDIT.md`
- This QA record: `docs/qa/BUILD_INTAKE_TO_QUOTE_PROCESS_AUTOMATION_AUDIT.md`

---

## PASS / FAIL

**PASS** — every major visible input in the intake-to-quote flow is inventoried with keep/auto-fill/infer/delay/remove guidance; automation ranked by confidence; illogical UI documented; ideal flow and prioritized plan explicit; next build recommended without mixed feature implementation.
