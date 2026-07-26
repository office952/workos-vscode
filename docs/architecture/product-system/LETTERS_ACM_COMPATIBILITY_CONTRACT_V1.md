# LETTERS ↔ ACM Compatibility Contract v1

**Status:** `ACCEPTED` — owner ACCEPT 2026-07-23 (`LETTERS_ACM_COMPATIBILITY_CONTRACT_V1_ACCEPTED`); **AMEND unity** 2026-07-23 (shared mounting spine)  
**Authority:** Product System / composition teaching. Not Offer, not Execution write path.  
**Templates:** `TPL-VOLUMETRIC-LETTERS` ↔ `TPL-ACM-BOXED-MOUNTING-SUPPORT` (Alucobond casetat).

Related (do not duplicate — cite):

| Concern | Canonical |
|---------|-----------|
| Direction / Composer | `docs/worklog/realignment/decision__letters_acm_compatibility_composer_direction_v1.md` |
| Shared mount spine (bare / with support) | `VOLUMETRIC_LETTERS_WITH_REAR_SUPPORT_MEMORIU.md` T11–T18 |
| Wall / no rear support branch | `VOLUMETRIC_LETTERS_WITHOUT_REAR_SUPPORT_MEMORIU.md` |
| Support ⊥ Mounting split | `VOLUMETRIC_LETTERS_PHASE_2_SUPPORT_MOUNTING_CONTRACT_ALIGNMENT.md` |
| Cables commercial default | Phase 2 **PH2-OD-09** (1 m 2×0.75 / literă; 5 m 2×1.5 220V) |
| Șablon pe ACM + 220V ownership | MIXED §§13–14 |
| Teaching SoT | `lettersAcmCompositionTaskOrder.ts`, `lettersAcmCompositionSablonProcess.ts` |
| Connection price sheet | `lettersAcmCompositionConnectionPrices.ts` · UI `structure/conexiune-litere-acm-preturi` |
| AI price fill evidence | `docs/worklog/realignment/2026-07-23_letters_acm_connection_prices_ai_proposed.md` |

---

## 1. Purpose

Declare the **Alucobond casetat surface delta** for mounting volumetric letters — not a second mounting philosophy.

Montajul pe bond este **același model** ca pe bare / alte suprafețe de suport: șablon → Forex pe suport → electric + traf + cablu → test → corp pe Forex → pack.  
Acest document blochează doar **ce diferă** când suportul este Alucobond casetat, plus legătura Composer între două Product Template-uri curate.

---

## 2. Shared mounting spine (unitate — toate suprafețele)

Owner memoriu (with rear support) — nucleul comun:

```text
T09–T10  LED + 1 m jumper pe Forex          ← Litere, indiferent de suport
T12      Șablon (interfață poziționare)     ← Litere-owned
T13      Prindere Forex pe suport           ← pe suprafața aleasă
T14–T16  Legături + PSU + cablu 220V        ← pe / în suport (unde e cazul)
T17      Test lumină
T18      Corp (plexi + volum) pe Forex
T19…     Finisaje / pack conform variantei
```

**Reguli comune (nu se reinventează aici):**

- Șablonul e al Literelor (`sablon_montaj`), nu card în nucleul suportului.
- Forex + LED + jumpers **înainte** de prinderea pe suport.
- Corp pe Forex **după** test (pe path cu suport / composition).
- Cabluri: **PH2-OD-09** + memoriu T10/T16 — nu o a treia speță în acest contract.
- Support fabrication (bare / ACM / …) e a **template-ului de suport**, nu a nucleului Litere.
- Phase 2: **support_*** ⊥ **mounting_*** — nu colapsa în `mounting_system` enum.

Fără suport (perete): memoriu without-support — T11–T16 inactive; T10 + T17 + T18 rămân. Nu e „alt produs”, e **ramură** a aceluiași spine.

---

## 3. Surface delta — Alucobond casetat (acest contract)

| Pas comun | Pe bare / premount (memoriu) | Pe Alucobond casetat (delta) |
|-----------|------------------------------|------------------------------|
| Suport gata | Bare / structură premount | ACM tasks 1–9 **fără pack** |
| Șablon T12 | Hartie print (memoriu default bare) | Autocolant transparent + transfer (MIXED §13) |
| Șablon comercial | MAT-SABLON / CNC path istoric | **Un proces 20 EUR/mp** pe **outbox layer integral** |
| T13 Forex pe suport | Autoforante pe bare | Autoforante pe bond; forme pline rămân sub Forex |
| T14–T16 electric | Pe bare; traf ascuns spate litere | **În carcasa bond** + traf; fără canal cablu tip bare |
| T16 cablu | ≥5 m 2×1.5 (PH2-OD-09) | **Același default** — nu reinventa |
| T17 test | Da | Da — înainte de corp |
| T18 corp | Pe Forex pe bare | Pe Forex pe bond; autoforante fine vopsite cant/volum |
| Pack | După ansamblu pe bare | **Un pack composition**; skip pack ACM early |

### Preconditions (ACM row)

| Side | Ready when |
|------|------------|
| **Alucobond casetat** | Tasks 1–9 done; **no pack yet** |
| **Litere** | Face, cant, Forex+LED+jumpers ready; body after backs on bond |

### Interface = șablon (ACM material + rate)

- Owner: Litere. Not an ACM nucleus card.
- Material ACM: transparent vinyl + transfer.
- Rate: **20 EUR/mp** bundled (material+cutter+transfer+apply).
- Qty: **outbox letters as integral layer** — not per-piece sum.

### Sequence on ACM (same spine, surface wording)

```text
1  Finalize Alucobond (no pack)           ← support ready
2  Șablon process on bond                 ← T12 + ACM delta rate
3  Fasten Forex on bond                   ← T13
4  Electric inside cassette + PSU         ← T14–T15 delta locus
5  Supply cable 5 m @ 220V                ← T16 = PH2-OD-09
6  Light test                             ← T17
7  Attach body to Forex                   ← T18
8  Pack composite                         ← pack once
```

---

## 4. Cost ownership (ACM connection lines) — price sheet

**UI SoT:** `/product-system/products/{ACM|Litere}/structure/conexiune-litere-acm-preturi`  
**Code:** `lettersAcmCompositionConnectionPrices.ts`

| Line | Tarif | Unit / bază | Decizie |
|------|-------|-------------|---------|
| Proces șablon | **20 EUR/mp** | outbox layer integral | **OWNER_LOCKED** |
| Prindere Forex pe bond | **8 EUR/mp** | outbox layer | **OWNER_VERIFIED_COHERENT** (2026-07-23) |
| Electrică + legare traf în carcasă | **35 EUR/buc** | 1 ansamblu (fără SKU PSU) | **OWNER_VERIFIED_COHERENT** |
| Cablu 5 m 220V (2×1.5) + atasare | **6 EUR/buc** | PH2-OD-09 default | **OWNER_VERIFIED_COHERENT** |
| Test lumină | **8 EUR/buc** | 1 ansamblu | **OWNER_VERIFIED_COHERENT** |
| Prindere corp pe Forex (șuruburi fine vopsite) | **12 EUR/mp** | outbox layer | **OWNER_VERIFIED_COHERENT** |
| Pack ansamblu | **10 EUR/mp** (min. **15 EUR**) | outbox layer | **OWNER_VERIFIED_COHERENT** |

Nu orar. Nucleu ACM (1.5 / 3.0 EUR/ml, 15 EUR/mp asamblare casetă) și materiale Litere/LED/PSU rămân pe template-urile lor.

---

## 5. Compatibility matrix

| From | To | Role |
|------|-----|------|
| Litere | Alucobond casetat | **This surface-delta contract (v1)** |
| Litere | Bare / premount | Same spine — memoriu with-support; future surface-delta doc in same shape |
| Litere | Wall-only | Same spine — memoriu without-support branch |
| **Alucobond casetat alone** | — | **Offerable root** (panel-only / vinyl / decorative / other content later) — decision §8 Q2 |
| ACM + other letter models | — | Future composition rows; same ACM root, different content contracts |
| Multiple products on one offer | — | **Allowed as separate commercial lines** (decision §8 Q3); one freeze = one product/composite |
| **Invoice / offer line name (this composition)** | — | **Final product:** `Litere volumetrice premontate pe suport de Alucobond` + cotă (cm/mm) — decision §8 Q3b |

v1 **implements/locks** only the ACM row. Other rows already have memoriu truth; do **not** fork a second mounting model when documenting them later — copy this delta pattern.

---

## 6. Non-goals

- Parallel „montaj ACM” philosophy separate from T12–T18
- Rewriting PH2-OD-09 cable specs here
- Composer UI / CostEngine / Offer / Execution writes
- Merging Letters + ACM into one Product Template

---

## 7. Intake / CPP honesty

**CPP v1 (2026-07-23):** composition lines `letters_acm_conn_*` @ owner rates when `applied_content=letters` on ACM; bundled șablon **20 EUR/mp**; legacy `sablon_montaj_*` suppressed under composition. Qty prefers `letters_layer_outbox_m2` (fallback `mounting_template_area_m2` with warning).

**Still gap:** CostEngine BOM `MAT-SABLON-*` + time CNC; Intake UI field for canonical outbox; EIC mirror.

---

## 8. Acceptance

| Field | Value |
|-------|-------|
| **Verdict** | `ACCEPTED` (+ unity AMEND 2026-07-23) |
| **Evidence** | `docs/worklog/realignment/2026-07-23_letters_acm_compatibility_contract_v1_accepted.md` |

**Locked:** shared spine = memoriu T12–T18 · ACM = surface delta · șablon 20 EUR/mp outbox integral · cables = PH2-OD-09.

**Price sheet:** complete on PS; șablon OWNER_LOCKED; 6 lines **OWNER_VERIFIED_COHERENT** (owner 2026-07-23 — coerent momentan).

**Next GO:** Finish Contract ACM Intake · Composer mock · CostEngine wiring.
