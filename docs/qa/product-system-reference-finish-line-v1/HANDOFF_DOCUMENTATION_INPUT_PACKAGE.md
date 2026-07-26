# Handoff documentation input package

Feed for the future 24-doc documentation build. Facts only — no offer/Execution.

## Freeze facts

1. Lab stop = **production cost (EIC)**, not offer/markup/order/Execution.
2. Product System modularity verdict: **MODULAR_WITH_GAPS**.
3. Form System verdict: **USABLE_WITH_TEMPLATE_GAPS** (VL Intake V6 = reference path, not universal UI).
4. Authoring: **Option 2** — edit links in UI; add-child via API/seed.
5. Analyzer: `workflow_adv_analyzer_io_contract_v1` — observe/propose only; operator confirms; no parser in WorkOS.
6. Critical material (missing price): **MAT-LED-PSU-12V**.
7. VL breakdown proof: internal **923.2**, commercial **1061**, reconcile OK.
8. Volum Aluminiu proves child ownership of cant truth.
9. Supplier Import deferred / Workflow-ADV only.
10. No ComponentTemplate parallel entity required.

## Canonical APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/product-system/reference-finish-line/contract` | Full finish-line package + CE map |
| `GET .../form-field-ownership-map` | 26 VL fields with source/destination/affects |
| `GET .../analyzer-io-contract` | Analyzer I/O freeze |
| `GET .../critical-materials` | Classification + manual-fill |
| `POST .../templates/{code}/price-breakdown` | EIC/CPP explainable breakdown |

## Evidence roots

- `docs/qa/product-system-reference-finish-line-v1/`
- `docs/qa/product-price-breakdown-v1/`
- `docs/qa/material-market-price-registry-v1/`
- Prior master audit (accepted with observations)

## Do not transfer as authority

- VL-only specialized UI pages as universal Form Generator
- Hardcoded template-code page copies
- Analyzer → Product Truth without confirmation
- CPP as lab completion for offer
- Invented material prices / Supplier Import stubs
