# RUNTIME_PROOF

## Stack

- Frontend: `http://127.0.0.1:3000` (detached)
- Backend: `http://127.0.0.1:8000` health 200

## Canonical route

- URL: `/intake-v6/5f853492-6a11-42c7-969f-6e27b9ec2718/operator`
- Workspace: `IV6-091CA8F5`
- Steps: Layers → Review (`Configurare`) → Confirm (`Confirmare`, pas 3)
- Deep-link `?step=confirm` alone does not switch step; click progress **Confirmare**

## Ready commercial path (live workspace)

1. Open workspace Confirm step.
2. Dry-run: `pricing_status=V6_PRICED_DRY_RUN_READY`, gross `687.56 EUR`.
3. `offer_composition_readiness.canonical_gate=ready`, `commercial_composition_complete=true`, `offer_ready_to_freeze=false` (no ConfirmJobProductTruth pin).
4. Confirm UI: Ofertă client shows backend totals; handoff checklist may still block create CTA.
5. Screenshot: `screenshots/confirm-step-gate-blocked-v1.png` (handoff blocked; commercial composition present).

## A_CONFIRMED_FALSE (HTTP, no DB mutation)

POST `/api/v1/product-system/commercial-price-preview/TPL-VOLUMETRIC-LETTERS_v2`  
with GRADI_EUR_SAFE quote_input + `finish_setup.confirmed=false` + letter groups `confirmed=false`:

- `status=blocked`
- `complete_offer_total=null` / `COMMERCIAL_PRODUCT_BLOCKED`
- blocker `COMMERCIAL_CONFIGURATION_INCOMPLETE` (Oracal 8500 confirmed width)
- readiness unit: `commercial_composition_complete=false`, `canonical_gate=blocked`

## Expected gate text

- Incomplete commercial composition → Confirm status blocked + no official Ofertă money
- Blocked product rows → labeled composition-only / “nu este Ofertă client”
- Priced-write CTA disabled while dry-run not READY or handoff incomplete
