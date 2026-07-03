# Intake V6 — Product Truth

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Related:** `INTAKE_V6_MODULAR_FORM_CONTRACT.md`, audit 2026-06-30

---

## 1. Rolul sistemului

Intake V6 capturează **cererea clientului** și **configurația produsului** — geometrie, finisaje, iluminare, montaj, opțiuni — fără a decide prețul comercial final. Este **source of truth pentru produsul cerut** și punctul de start coerent al fluxului canonic.

**Regulă:** Intake V6 este coerent și trebuie construit plecând de la el. Nu se redesignează flow/layout fără GO owner.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Cererea** | Client, job title, deadline, context comercial operator |
| **Configurația produsului** | Template binding, finish setup, module activation |
| **Dimensiuni** | width_mm, height_mm, depth_mm, bbox |
| **Geometrie** | quote_geometry, path_geometry_summary, letter_count, perimeter, areas |
| **SVG / analiză geometrică** | svg_source, svg_analysis_json, layer_role_setup |
| **Finisaje** | face_finish_type, return_finish_type, letter_group_finishes, RAL/vinyl |
| **Iluminare** | illuminated, lighting_system_type, led_module_count, PSU |
| **Montaj** | mounting_template, mounting_system, mounting_bar_profile |
| **Opțiuni** | backing_mode, structură suport (dacă selectată), flags |
| **Date client** | client_name, contact — workspace payload |
| **Product request** | Starea cererii, confirmations, readiness gates |
| **Commercial inputs (operator)** | markup, discount, VAT — **input operator, nu truth comercial** |

**Persistență:** `intake_v6_workspaces.payload_json`

---

## 3. Ce NU detine

| Exclus explicit |
|-----------------|
| Preț comercial final / oferta oficială |
| CostEngine final / CostResult canonic |
| CommercialPriceProposal runtime |
| Taskuri reale / ExecutionPlan |
| ProfitabilityAnalysis |
| Minute reale / ExecutionActuals |
| HR / pontaj / cost angajat |
| Reguli comerciale definitive (mp/ml/buc) — doar input pentru propunere |
| ProductDefinition compilat (produce input, nu îl stochează ca truth final) |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Operator | Finish choices, confirmations, commercial_inputs |
| SVG upload | Geometrie, layer roles |
| SVG analyzer | quote_geometry sync, metrics |
| ProductSystem (read-only) | template_code, module availability hints |
| Client context | Nume, dimensiuni manuale |

**API-uri tipice (read context):** workspace CRUD, finish-setup, svg analysis, material-breakdown (preview), pricing-input-preview (ephemeral).

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Workspace payload canonic | ProductDefinition builder |
| quote_input adapter fields | Quote draft notes, /price path (frozen intent) |
| Date geometrie/finisaj | CommercialPriceProposal (viitor 7G) |
| Date geometrie/materiale | EstimatedInternalCost |
| Draft quote linkage | Quote notes (`quote_input_payload`) — **fără preț oficial** |
| Gates / readiness | Confirm step, owner approval |

**Produce input canonic pentru:** ProductDefinition, CommercialPriceProposal, EstimatedInternalCost, quote draft.

**NU produce:** priced snapshot, product_definition frozen, execution_plan.

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Product cerut (config + geometrie) | **Source of truth** |
| Preț comercial | **NOT** — preview only |
| Cost intern | **NOT** — breakdown ephemeral |
| Taskuri | **NOT** — preview dry-run |

---

## 7. Conexiuni cu celelalte sisteme

```
Intake V6 (product truth)
    ↓ workspace + quote_input
ProductDefinition ← compilează module active din Intake + Template
    ↓
ProductAggregate ← expandează parent + dossier + modules
    ↓
CommercialPriceProposal ← citește geometrie + config (nu minute)
EstimatedInternalCost ← citește aggregate + inventory
    ↓
Quote draft (notes) → priced snapshot (Step 8) → Order → ExecutionPlan → Actuals
```

| Legătură | Direcție |
|----------|----------|
| → ProductSystem | Citește template_code, constraints |
| → ProductDefinition | Furnizează workspace + quote_input |
| → Quote (draft) | `create-draft-quote` — grand_total=0 by design |
| ← ProductSystem | NU scrie în template |

---

## 8. Reguli owner obligatorii

1. Intake V6 = product truth — **păstrat**, fără redesign fără GO.
2. **Live offer** (`intakeV6OfferCalculator`) = **preview intern**, nu oferta oficială.
3. Nu afișa preview ca „preț final client” fără etichetă (Step 11).
4. Confirm creează draft quote **fără** `/price` obligatoriu — separare intenționată până la Step 8.
5. No hourly commercial pricing — Intake nu calculează ore × tarif ca ofertă.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Preview ≠ quote | Live ~6324 RON vs grand_total=0 | `MISLEADING_UI` |
| Breakdown ephemeral | Material breakdown nu persistă | OK pentru preview |
| Client-side offer calc | `intakeV6OfferCalculator.ts` — cost buckets + markup | `HIGH_RISK_WRONG_DIRECTION` dacă tratat ca oficial |
| quote_input vs parent BOM | Câmpuri reach quote_input dar parent template gol | `DEAD_PIECE` downstream |
| Task preview parallel | V3 catalog, nu ProductDefinition | `DEAD_PIECE` |
| commercial_inputs în workspace | Markup/VAT pot confunda cu CommercialPriceProposal | `NEEDS_OWNER_DECISION` |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Workspace | Rămâne truth produs — complet, versionat logic |
| Preview panels | Etichetate „estimare internă / preview comercial” |
| Confirm → draft | Linkage clar; fără pretins oficial până snapshot Step 8 |
| quote_input | Adapter stabil către ProductDefinition |
| Gates | Blochează confirm dacă geometrie/critical fields lipsesc |
| Fără redesign | Flow SVG → Review → Confirm păstrat |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Tratarea live offer ca quote oficial |
| Scrierea prețului comercial în workspace ca truth |
| Generarea ExecutionPlan din Intake |
| Modificarea ProductSystem templates din Intake |
| Implementare CommercialPriceProposal în Intake fără Step 7G scoped |
| Redesign UI/flow fără GO owner |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Product fields documentate | Toate zonele volumetric mapped |
| Separare preview vs official | Documentat + UI labels (Step 11) |
| Output către ProductDefinition | Contract quote_input stabil |
| No commercial truth in Intake | Cod + docs aliniate |
| Owner gates respected | Fără GO → fără runtime change |

**Endpoint/model țintă (conceptual):**

- `GET/PUT /api/v1/intake-v6/workspaces/{id}` — workspace truth
- `GET .../pricing-input-preview` — **preview_only**, read-only
- `POST .../create-draft-quote` — draft fără preț oficial
- **NU** endpoint nou de preț comercial în Intake — CommercialPriceProposal separat (7G)
