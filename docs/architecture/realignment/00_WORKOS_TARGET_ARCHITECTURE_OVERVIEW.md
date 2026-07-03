# WorkOS — Target Architecture Overview

**Version:** 1.0.4  
**Status:** Target architecture + **runtime alignment notes** (sync 2026-06-30 after Step 9 persist draft validation)  
**Date:** 2026-06-30  
**Audit verdict accepted:** `HIGH_RISK_DEVIATED` / `HIGH_RISK_MINUTES_AS_PRICE`

---

## 1. Rolul sistemului

WorkOS este sistemul intern P-Media pentru fluxul complet: **cerere → produs → ofertă → comandă → producție → actuals → analiză post-job**. Acest document descrie **imaginea mare** a arhitecturii țintă — separarea sistemelor, fluxul canonic și interdicțiile globale.

WorkOS **nu** este workos.com (AuthKit/SSO). WorkOS intern = ERP manufacturing/signage P-Media.

---

## 2. Ce detine (la nivel de platformă)

| Domeniu | Responsabilitate |
|---------|------------------|
| **Product truth** | Intake V6 → ProductDefinition → ProductAggregate |
| **Commercial truth (țintă)** | CommercialPriceProposal + Quote snapshot |
| **Internal cost truth (țintă)** | EstimatedInternalCost (separat de comercial) |
| **Execution truth** | Order → ExecutionPlan → ExecutionActuals |
| **People truth (intern)** | HR, pontaj, angajați — nu preț client |
| **Material truth** | Inventory Material Registry (achiziție/stoc) |
| **Learning truth (țintă)** | ProfitabilityAnalysis post-job |
| **Governance** | Reguli owner, freeze paths, roadmap 7G–12 |
| **Order financial immutability (Slice 10.1)** | PUT guard on locked/V2 orders — **IMPLEMENTED** |

### Runtime alignment snapshot (2026-06-30)

| Area | Status | Notes |
|------|--------|-------|
| Order Snapshot V2 | **VALIDATED** | `accepted_commercial_total`, `estimated_internal_total`, `no_reprice_policy=True` |
| Execution Plan V2 envelope | **VALIDATED** | `planned_tasks[]` informative; `operational_tasks[]` after materialize |
| ExecutionReality / sessions | **VALIDATED** | Starts at `start-task`; materialize does **not** create sessions |
| Order financial PUT guard | **IMPLEMENTED + VALIDATED** | Slice 10.1 individual (`90ba918`); batch `PUT /orders/batch` (`453932f`) — same `order_immutability_service` |
| ProfitabilityAnalysis read-only API | **IMPLEMENTED + VALIDATED** | Slice 10.2+10.3 — `GET /api/v1/profitability-analysis/order/{order_id}`; minimal ExecutionDetail panel (`378b42b`) |
| Dual Quote Snapshot V2 (Step 8) | **VALIDATED_WITH_GUARDS** | Live chain **VALIDATED**: freeze → pricing review from snapshot V2 → owner approval → accept → convert; order `88002`; convert creates **no** plan/tasks; **no** `/price`/CE/QO |
| ExecutionPlan V2 preview (Step 9) | **VALIDATED** | `POST .../execution/plan-v2/preview/{order_id}` from `orders.snapshot_v2_json`; order `88002`; READINESS_GATE excluded; **no** DB writes |
| ExecutionPlan V2 persist draft (Step 9) | **VALIDATED_WITH_GUARDS** | `POST .../execution/plan-v2/from-order/88002` — plan `id=2`, `source_quote_snapshot_v2_id=3`; **107 pytest**; idempotency `already_exists`; **no** execution_tasks/sessions; HTTP QA **pending backend restart** |
| Task materialize / sessions (Step 9+) | **BLOCKED** | `materialize-tasks` and Step 11 sessions **NEEDS OWNER GO** |
| CommercialPriceProposal runtime (7G) | **NOT STARTED** | Preview services only |
| Batch PUT `/orders/batch` financial guard | **MITIGATED** | Was **WATCH** after Slice 10.1 — **IMPLEMENTED + VALIDATED** in `453932f` (fail-closed pre-flight) |

---

## 3. Ce NU detine

| Interzis la nivel platformă |
|-----------------------------|
| Preț comercial calculat universal ca `minute × tarif oră` |
| O singură cifră „finală” fără separare comercial / intern / actual |
| HUB extern (colaboratori, marketplace) — doar boundary viitor |
| Decizii de implementare fără GO owner |
| Rescriere retroactivă a ofertei acceptate din ExecutionActuals |

---

## 4. Inputuri

| Sursă | Rol |
|-------|-----|
| Operator Intake V6 | Cerere produs, geometrie, finisaje |
| ProductSystem templates | Reguli tehnologice posibile |
| Pricing Registry (separat) | Reguli comerciale + cost materiale |
| Inventory | Cost achiziție materiale |
| Production floor | Task sessions, consum real |
| HR / Pontaj | Cost intern angajat (analiză) |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Quote snapshot (dual) | Client, Order |
| Order frozen snapshot | ExecutionPlan |
| ExecutionPlan tasks | Operator, Employee Mobile |
| ExecutionActuals | ProfitabilityAnalysis, capacitate |
| ProfitabilityAnalysis | Owner — tuning reguli viitoare |

---

## 6. Source of truth

```
┌─────────────────────────────────────────────────────────────────┐
│ PRODUCT TRUTH                                                    │
│   Intake V6 → ProductDefinition → ProductAggregate               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ COMMERCIAL PRICE TRUTH — TARGET                                  │
│   CommercialPriceProposal (mp/ml/buc/literă/set/minim)           │
│   ❌ Today: QuotePrice.final from cost_plus (/price)             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ESTIMATED INTERNAL COST — TARGET (partial today, mixed)          │
│   EstimatedInternalCost — materials + ops non-hourly + overhead  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ EXECUTION ACTUALS                                                │
│   execution_reality, task sessions — real minutes post-order     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PROFITABILITY — PARTIAL (read-only API VALIDATED)                │
│   ProfitabilityAnalysis — quoted vs estimated vs actual          │
│   GET /api/v1/profitability-analysis/order/{order_id}            │
│   actual cost/margin null in MVP — HR/inventory costing deferred │
└─────────────────────────────────────────────────────────────────┘
```

**Guardrail:** Niciun strat nu substituie silent alt strat (ex. minute reale → preț quote; `unit_cost` material → preț mp client fără regulă comercială).

---

## 7. Conexiuni cu celelalte sisteme — Fluxul canonic

```
Intake V6
    ↓  (product request, geometry, finishes, LED, mounting)
ProductDefinition
    ↓  (module active/inactive, canonical config, readiness)
ProductAggregate
    ↓  (technical graph: components, materials, operations)
    ├──────────────────────────┬──────────────────────────┐
    ↓                          ↓                          ↓
CommercialPriceProposal   EstimatedInternalCost     (shared geometry keys)
    ↓                          ↓
    └──────────────┬───────────┘
                   ↓
            Quote Snapshot (Step 8)
         commercial + internal + warnings
                   ↓
                 Order (frozen)
                   ↓
            ExecutionPlan (tasks from technical graph)
                   ↓
            ExecutionActuals (real minutes, materials)
                   ↓
            ProfitabilityAnalysis (post-job learning)
```

### Unde intră fiecare sistem

| Sistem | Poziție în flux |
|--------|-----------------|
| **Intake V6** | Start — product truth pentru cererea clientului |
| **ProductSystem Template** | Upstream registry — ce module/operații sunt posibile |
| **ProductDefinition** | Compiler — activează dependentele pentru produsul concret |
| **ProductAggregate** | Read model — graful tehnic complet expandat |
| **CommercialPriceProposal** | Pre-ofertă — ce propunem clientului (mp/ml/buc/set) |
| **EstimatedInternalCost** | Pre-ofertă — ce credem că ne costă intern |
| **Quote / Order** | Snapshot înghețat — promisiune comercială + estimare internă |
| **ExecutionPlan** | Post-order — taskuri operaționale din graf |
| **ExecutionActuals** | Producție — minute reale, materiale reale |
| **ProfitabilityAnalysis** | Post-job — învățare, fără rescriere ofertă |

---

## 8. Reguli owner obligatorii

1. **No hourly commercial pricing** — P-Media nu ofertează „ore × tarif”.
2. **Minutele** sunt doar ExecutionActuals / capacitate / statistică / ProfitabilityAnalysis.
3. **Cost intern estimativ ≠ oferta finală** către client.
4. **Snapshot ofertă** = comercial + intern **separat**, side-by-side.
5. **Doar ownerul** decide modificări — fără GO, fără implementare.
6. **Intake V6 rămâne product truth** — construim plecând de la el.
7. **WorkOS intern vs HUB extern** — HUB nu se implementează acum.
8. **Fără reset DB / reseed** ca soluție implicită.
9. **Fără UI redesign** fără GO + audit vizual.
10. **Fără quote 4 reprice** până la traseu 7G→8.

---

## 9. Riscuri actuale din audit

| Risc | Manifestare | Clasificare |
|------|-------------|-------------|
| Minute = preț | Cost Engine `per_hour`; QuoteOrchestrator `total_cost × margin` | `HIGH_RISK_WRONG_DIRECTION` |
| `/price` mixed | Un endpoint amestecă cost intern + preț comercial | `FROZEN_UNTIL_REALIGNED` |
| Lipsă CommercialPriceProposal | Nu există model runtime mp/ml/buc/set | `NEEDS_OWNER_DECISION` |
| Preview ≠ quote | Intake live offer ~6324 RON; draft quote `grand_total=0` | `MISLEADING_UI` |
| Parent template gol | `components_json=[]`; dossier audit-only | `DEAD_PIECE` |
| Taskuri paralele | V3 catalog vs product_definition vs execution_plan | `DEAD_PIECE` / fragmentare |
| Pricing Registry hub | Material + WC rates + markup unificat | `HIGH_RISK_WRONG_DIRECTION` |
| ProfitabilityAnalysis actual margin $ | Read-only GET **VALIDATED**; `actual_margin_*` **null in MVP** — HR/inventory costing deferred | Step 10 partial |
| PUT orders financial mutation | Was possible on locked/V2 | **MITIGATED** — individual PUT Slice 10.1 (`90ba918`); batch PUT was **WATCH**, closed in `453932f` |

---

## 10. Target state

WorkOS trebuie să se bazeze pe **produs**, **reguli comerciale** și **realitate operațională** — nu pe timp ca unitate comercială.

| Model | Rol țintă |
|-------|-----------|
| CommercialPriceProposal | Preț client: mp, ml, buc, literă, set, minim, complexitate |
| EstimatedInternalCost | Estimare internă: materiale + ops non-orare + overhead |
| ExecutionActuals | Realitate: minute, materiale, angajați |
| ProfitabilityAnalysis | Comparație post-job; recomandări viitoare |

**Separare clară:** `CommercialPriceProposal ≠ EstimatedInternalCost ≠ ExecutionActuals ≠ ProfitabilityAnalysis`

Exemple owner (litere volumetrice):

| Zonă | Basis comercial |
|------|-----------------|
| CNC | lei/ml — material, grosime, sanfren |
| Modelare cant | lei/ml |
| Vopsire/finisaj | lei/m² sau minim lucrare |
| LED | lei/modul, set sau mp luminat |
| Asamblare | lei/literă/set/pachet |
| Montaj | fix / per locație — **nu** automat oră |

---

## 11. Forbidden behavior (global)

| Interzis | Motiv |
|----------|-------|
| `POST /price` ca „fix” fără realiniere | Mixed model |
| Reprice Quote 4 | Frozen |
| Apply Step 7E.2 fără GO | Payload repair out of scope |
| Cost Engine rewrite ad-hoc | Step 7H scoped |
| `rate_per_hour` ca basis comercial | Owner law |
| `total_internal_cost × margin` universal | Cost-plus |
| Live Intake offer = oferta oficială | Preview ≠ snapshot |
| Minute reale → modificare quote acceptat | Retroactiv interzis |
| Taskuri din catalog paralel | Trebuie din ProductDefinition/Aggregate |
| Implementare 7G+ fără GO owner | Governance |

---

## 12. Acceptance criteria

| Criteriu | Verificare |
|----------|------------|
| Flux documentat end-to-end | Toate nodurile 01–16 au contract |
| Separare 4 lumi | Comercial / intern / actuals / profitability distinct |
| No-hourly guard | Documentat în fiecare sistem relevant |
| Freeze paths listate | `/price`, orchestrator, per_hour frozen intent |
| Owner GO gates | Fiecare step 7G–12 marcat NEEDS GO |
| Legacy clasificat | Tag-uri în doc 19 |
| UNKNOWN marcat | Fără presupuneri (ex. debitare spate: ml vs m²) |

---

## Roadmap recomandat (awareness)

| Step | Focus |
|------|-------|
| **7G** | CommercialPriceProposal read-only preview |
| **7H** | EstimatedInternalCost non-hourly |
| **7I** | Pricing Registry separation |
| **8** | Quote snapshot dual |
| **9** | ExecutionActuals hardening |
| **10** | ProfitabilityAnalysis |
| **11** | UI labels (no redesign) |
| **12** | Dead pieces cleanup (owner decision) |

Detalii: [20_ROADMAP_STEPS_7G_TO_12.md](./20_ROADMAP_STEPS_7G_TO_12.md)

---

## Separarea sistemelor (rezumat)

| Sistem | Detine | NU detine |
|--------|--------|-----------|
| Intake V6 | Cerere, config produs | Preț comercial final |
| ProductSystem | Template, dependențe posibile | Alegere concretă job |
| ProductDefinition | Module active, readiness | Preț, taskuri reale |
| ProductAggregate | Graf tehnic | Preț comercial |
| CommercialPriceProposal | Preț client mp/ml/buc | Minute, actuals |
| EstimatedInternalCost | Cost intern estimat | Preț client obligatoriu |
| Cost Engine (țintă) | Calculator cost intern | Generator preț comercial |
| Quote/Order | Snapshot înghețat | Recalcul retroactiv |
| ExecutionPlan | Taskuri, ordine | Preț comercial |
| ExecutionActuals | Minute reale | Modificare quote |
| ProfitabilityAnalysis | Marjă reală, recomandări | Rescriere ofertă |
