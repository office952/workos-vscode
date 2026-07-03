# Intake V6 Modularization Audit

**Version:** 1.0.0  
**Date:** 2026-07-01  
**Status:** Architecture audit + spike direction  
**Pilot template:** `TPL-VOLUMETRIC-LETTERS_v2` (aliases: `TPL-VOLUMETRIC-LETTERS`)  
**Companion docs:** [01_INTAKE_V6_PRODUCT_TRUTH.md](./realignment/01_INTAKE_V6_PRODUCT_TRUTH.md), [INTAKE_V6_MODULAR_FORM_CONTRACT.md](./INTAKE_V6_MODULAR_FORM_CONTRACT.md), [MODULAR_PRODUCT_FLOW_CONTRACT.md](./MODULAR_PRODUCT_FLOW_CONTRACT.md)

---

## 1. Executive summary

Intake V6 today delivers a strong **volumetric letters** operator experience, but much of the capture UI, review layout, and pricing handoff is **template-hardcoded**. Adding a second product (face/back prep, CNC cutting, flat signage) would require copying large React surfaces rather than registering a product plugin.

**Recommendation:** split Intake V6 into:

1. **Intake V6 Core** — workspace lifecycle, steps (Straturi → Review → Confirm), modular form contract consumption, readiness gates, quote handoff spine, snapshot V2.
2. **Product Plugin** — per `template_code`: capture sections, review tabs, dossier field mapping, pricing-input adapter hooks.
3. **Shared downstream** — ProductDefinition → ProductAggregate → Commercial Price Proposal → CostEngine (unchanged boundary).

This document captures a live trace audit, the canonical truth model, coupling inventory, and the first spike (`IntakeV6ProductPlugin` registry).

---

## 2. Live trace (gradi-curat.svg)

**Workspace:** `IV6-39530B87` (`9e2ed965-35f0-4cef-b6f7-22120c539397`)  
**Asset:** `gradi-curat.svg` (19 letters, ~5087×600 mm bounding box)

| Step | UI label | What operator sees | What gets written / computed |
|------|----------|-------------------|------------------------------|
| 1 — Straturi | Layer roles, SVG upload | Path geometry, letter grouping | `payload_json.svg_source`, `path_geometry`, `layer_role_setup` |
| 2 — Review | Finisaje / Iluminare / Montaj | Finish assignment, LED, mounting | `payload_json.finish_setup`, module activation via form contract |
| 2 — Review (preview) | Pricing input preview | “Ready”, letter count, dimensions | Ephemeral — `GET .../pricing-input-preview` |
| 2 — Review (preview) | Material breakdown | ~771 EUR materials | Ephemeral — not commercial truth |
| 2 — Review (preview) | Calcul live | ~6324 RON estimate | **Non-official** — operator aid only |
| 3 — Confirm | Handoff readiness | Blockers, aggregate preview | Gates `priced-quote/dry-run` and `priced-quote/write` |
| Quote detail | Commercial spine | Dry-run → write → Snapshot V2 | Official price only after write + snapshot |

**Fresh audit workspace:** `IV6-9B8E756B` (`5b2d6d6a-c542-4371-a65a-dbbec30983f1`) — same SVG uploaded via API for repeatable traces.

---

## 3. Canonical truth model

```
┌─────────────────────────────────────────────────────────────────┐
│ intake_v6_workspaces.payload_json  ← PRODUCT TRUTH (operator)   │
│   svg_source, path_geometry, finish_setup, quote_geometry, …    │
└────────────────────────────┬────────────────────────────────────┘
                             │ modular form contract + adapters
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ pricing-input-preview / material-breakdown / live calc          │
│   EPHEMERAL — UX aids, not quote or order truth                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ priced-quote/write (when ready)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Quote Snapshot V2 + line items  ← COMMERCIAL TRUTH              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              ProductDefinition → Aggregate → CostEngine (internal)
```

### Truth boundaries (must not blur)

| Layer | Source | Consumer | Official? |
|-------|--------|----------|-----------|
| Operator product truth | `payload_json` | PD compiler, readiness | Yes (product) |
| Form contract | Registry + field bindings | Intake UI, activation preview | Yes (schema) |
| Pricing preview | Adapter + dev-bridge rates | Review UI | No |
| Live calculation | Client-side estimate | Review sheet | No |
| Commercial price | `priced-quote/write` + Snapshot V2 | Quotes, orders | Yes (commercial) |
| Internal cost | CostEngine (post-aggregate) | Profitability | Yes (internal) |

CostEngine is **not** in Intake CRUD by design — Intake stops at readiness + handoff; execution costing follows aggregate graph.

---

## 4. Downstream alignment

| System | Intake V6 relationship | Gap / note |
|--------|------------------------|------------|
| **Product System / Template** | `template_code` on workspace; dossier variant fields drive form options | Template onboarding still manual; no generic plugin slot |
| **Dossier** | `useTemplateFormContract` reads variant fields for volumetric | Other templates lack dossier → form bridge |
| **Modular Form Contract** | `GET /form-contract/{template_code}` — Step 5 read-only | Derived from registry + volumetric field map only |
| **ProductDefinition** | Built from payload + contract keys at confirm/handoff | Builder logic volumetric-centric |
| **ProductAggregate** | Full graph returned on confirm preview | Intake displays subset; no template-generic section registry |
| **Commercial Price Proposal** | `priced-quote/dry-run`, `priced-quote/write` | Dev-bridge prices (Step 8 QA), not Pricing Registry (Step 7I) |
| **CostEngine** | Referenced in contract `cost_engine_step` metadata | Not invoked from Intake workspace CRUD |
| **Quotes** | Snapshot V2 + commercial spine panel | V6-specific display paths in `Quotes.tsx` |

---

## 5. Coupling inventory (what breaks on second product)

### 5.1 Frontend — hardcoded volumetric

| Area | File(s) | Coupling |
|------|---------|----------|
| Review tabs | `IntakeV6ReviewTabNav.tsx` | Fixed Finisaje / Iluminare / Montaj |
| Review step body | `IntakeV6ReviewStep.tsx` | Large volumetric-only panels |
| Layers step | `IntakeV6LayersStep.tsx` | SVG layer roles for letters |
| Confirm | `IntakeV6ConfirmStep.tsx`, handoff panels | Volumetric readiness + aggregate display |
| Form contract hook | `useTemplateFormContract.ts` | TPL-VOLUMETRIC-LETTERS dossier |
| Quote bridge | `IntakeV6QuoteCommercialSpinePanel.tsx` | V6 priced-quote API (template-agnostic API, volumetric UX) |
| Field bindings | `VOLUMETRIC_FIELD_BINDINGS` (backend map) | Letters-only paths |

### 5.2 Backend — template-specific services

| Service | Role |
|---------|------|
| `intake_v6_modular_form_contract_service.py` | Registry + volumetric field map |
| `intake_v6_priced_quote_*_service.py` | Handoff (works if pricing input adapter is pluggable) |
| `commercial_rules_volumetric_v2.py` | Dev-bridge pricing |

### 5.3 What is already modular-friendly

- Workspace reducer + `payload_json` paths via form contract `workspace_path`
- Module activation preview (`intakeV6ModuleActivationPreview`)
- Readiness stages and gate vocabulary
- Quote Snapshot V2 contract (template code carried, not UI-specific)
- Modular form contract types (`IntakeV6ModularFormContractResponse`)

---

## 6. Target architecture

```
                    ┌──────────────────────┐
                    │   Intake V6 Core     │
                    │ steps, workspace,    │
                    │ readiness, handoff   │
                    └──────────┬───────────┘
                               │ template_code
                               ▼
                    ┌──────────────────────┐
                    │ IntakeProductPlugin  │
                    │ registry (FE + BE)   │
                    └──────────┬───────────┘
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
   captureStepSections   reviewTabSections   pricingInputAdapter
           │                   │                   │
           └───────────────────┴───────────────────┘
                               │
                               ▼
              Shared: form-contract, PD, aggregate, CPP, CostEngine
```

### 6.1 `IntakeProductPlugin` responsibilities

| Capability | Owner | Notes |
|------------|-------|-------|
| `templateCode` + aliases | Plugin | Resolve `TPL-VOLUMETRIC-LETTERS` → `_v2` |
| `reviewTabs` | Plugin | Tab id, label, icon, linked `module_codes` |
| `captureSteps` | Core | Plugin may hide/relabel steps later |
| `formContractSource` | Core | Always API; plugin does not duplicate bindings |
| `pricingInputAdapter` | Plugin (BE) | payload → quote input payload |
| `confirmSections` | Plugin | Optional ordered review blocks on confirm |
| `readinessRules` | Core + plugin extensions | Core gates; plugin adds module-specific blockers |

### 6.2 Non-goals (this phase)

- Rewriting `IntakeV6ReviewStep` into micro-frontends
- Moving all `VOLUMETRIC_FIELD_BINDINGS` to DB (track as Step 7I / registry work)
- Production Pricing Registry replacement for dev-bridge

---

## 7. Spike: frontend product plugin registry

**Location:** `frontend/src/lib/intakeV6/intakeV6ProductPlugin.ts`

**Delivered in spike:**

- Type `IntakeV6ProductPlugin` and `IntakeV6ReviewTabDefinition`
- Registry with pilot volumetric plugin
- `resolveIntakeV6ProductPlugin(templateCode)` with alias normalization
- `resolveIntakeV6ReviewTabs(templateCode)` — used by `IntakeV6ReviewTabNav`
- Unit tests for resolution and fallback

**Backend spike (same phase):**

- `backend/services/intake_v6_product_pricing_adapter_registry.py`
- `build_v6_pricing_input_preview(..., template_code=)` routes through adapter registry
- Workspace, handoff, and priced-quote dry-run pass `record.template_code`
- Tests: `backend/tests/test_intake_v6_product_pricing_adapter_registry.py`

**Next spikes (not in this commit):**

- Backend `ProductPricingInputAdapter` protocol + registry
- Plugin-driven confirm section ordering
- Second template stub (`TPL-VOLUMETRIC-FACE-BACK-PREP`) to prove non-volumetric tabs

---

## 8. Migration path

| Phase | Work | Outcome |
|-------|------|---------|
| **A — Registry** | FE plugin registry + review tabs (this doc) | Second product can declare tabs without editing nav |
| **B — Section extraction** | Split ReviewStep panels into plugin-keyed lazy components | Smaller volumetric file; hook point for new products |
| **C — BE adapter registry** | `pricing_input_adapter_for(template_code)` | Remove volumetric-only assumptions from priced-quote services |
| **D — Confirm modularization** | Plugin `confirmSections` + shared readiness | Confirm step reusable |
| **E — Pricing Registry** | Replace dev-bridge with owner-approved rates | Production commercial truth |
| **F — Template onboarding** | Playbook: dossier → contract → plugin → adapter | New product without Intake rewrite |

---

## 9. Recommendations

1. **Treat `payload_json` as the only operator product truth** — keep previews and live calc visibly non-official (already partially done in UI audit).
2. **Do not add product-specific branches in `Quotes.tsx`** — route through template code + snapshot schema version.
3. **Register products, don’t fork Intake** — every new `if (template === …)` in Review/Confirm is tech debt.
4. **Keep CostEngine out of Intake CRUD** — aggregate preview on confirm is sufficient boundary.
5. **Prioritize BE pricing adapter registry** after FE tab registry — handoff is the highest-risk coupling point.
6. **Unify template code aliases** at plugin resolution (`TPL-VOLUMETRIC-LETTERS` / `_v2`).

---

## 10. References

- **Integrare Oferte (soluție completă):** [BUILD_INTAKE_V6_QUOTES_INTEGRATION.md](../qa/BUILD_INTAKE_V6_QUOTES_INTEGRATION.md)
- Live quote verification: `Q-V6-IV6-BB8EE3F8` — dry-run → write → 2587.94 RON
- Integration branch: `fix/intake-v6-quotes-integration`
- UI audit targets: quote `Q-V6-IV6-39530B87`, workspace `IV6-39530B87`

---

## Appendix A — Review tab ↔ module mapping (pilot)

| Review tab | Module codes (contract) | Purpose |
|------------|-------------------------|---------|
| Finisaje | face, cant, artwork | Surface finishes and letter grouping |
| Iluminare | led, backing | Illumination options |
| Montaj | mounting, template | Installation system |

Plugin registry encodes this mapping so future templates can expose different tab sets (e.g. single “Pregătire” tab for face/back prep).
