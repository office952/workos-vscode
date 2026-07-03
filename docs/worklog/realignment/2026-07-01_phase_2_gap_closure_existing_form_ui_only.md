# Phase 2 Gap Closure - Existing Form UI-Only Pass

## Scope

Controlled Phase 2 pass for remaining existing-form visibility gaps. Existing Intake V6 Straturi / Review / Confirmare remains the source. This pass is UI-only/display-only and does not implement Product Truth runtime payload.

## Pre-edit detailed gap map

| Area | Existing UI component/file | Existing controls found | Existing helper/chip support | Current Product Truth candidate visibility | Owner-approved default visibility | Operator confirmation visibility | Quote/order/execution blocker visibility | Missing visibility | Missing actual control | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| Face / Plexiglas material | `IntakeV6ReviewLetterGroupsSection.tsx` | Face finish select, Oracal/color/roll controls | `facePlexiglas` | PARTIAL | Plexiglas opal 3 mm visible in chip | Operator confirmable chip visible | Required for quote visible | Explicit material wording should be clearer | Explicit face material control: NO | TOUCH_UI_DISPLAY_ONLY |
| Face / Plexiglas thickness | `IntakeV6ReviewLetterGroupsSection.tsx` | No thickness select | `facePlexiglas` | PARTIAL | 3 mm default visible in chip | Operator confirmable chip visible | Required for quote visible | 5 mm later exception and missing explicit control should be visible | Explicit thickness control: NO | DOC_ONLY_GAP + TOUCH_UI_DISPLAY_ONLY |
| Back / Forex | `IntakeV6ReviewBackingSelect.tsx` | `backing_mode` select | `backForex` | YES | Forex 10 mm default visible | Select is operator-editable | Required for quote visible | none major | NO | TOUCH_UI_DISPLAY_ONLY |
| Back sanfren | `IntakeV6ReviewBackingSelect.tsx` | Forex no/with sanfren option | `backForex` | YES | no-sanfren default visible | Select is operator-editable | Required for quote visible | wording can stay local | NO | TOUCH_UI_DISPLAY_ONLY |
| Return / Cant depth | `IntakeV6ReturnCantFields.tsx` via letter/artwork cards | Depth select | `returnCant` | YES | template/form default implied | field is operator-editable | Required for quote visible | owner-approved existing form rule can be clearer | NO | TOUCH_UI_DISPLAY_ONLY |
| Return / Cant color/RAL/finish | `IntakeV6ReturnCantFields.tsx`, `ColorRegistrySelect` | Finish family, RAL/Oracal color | `returnCant` | YES | existing form rule visible partially | field is operator-editable | Required for quote visible | RAL/Oracal/vopsit/alb/negru/aluminiu selectability can be clearer | NO | TOUCH_UI_DISPLAY_ONLY |
| Finish / Oracal series | `IntakeV6ReviewLetterGroupsSection.tsx` | face finish select | `finishOracalPrintLamination` | YES | existing form answer visible | field is operator-editable | Required for quote visible | Oracal 641/651/8500 explicit list can be clearer | NO | TOUCH_UI_DISPLAY_ONLY |
| Finish / Oracal color | `ColorRegistrySelect` in face/cant zones | color select when required | `finishOracalPrintLamination` | YES | existing form answer visible | field is operator-editable | Required for quote visible | color required when active should be clearer | NO | TOUCH_UI_DISPLAY_ONLY |
| Finish target: fata/cant/artwork/spate/all | Face/Cant/Artwork zones; Back select | target is implied by zone | `finishOracalPrintLamination`, `returnCant`, `artworkPrintedArtwork`, `backForex` | PARTIAL | zone-based target visible by UI layout | operator confirms fields, not canonical target | Required for quote visible | explicit target chips: fata/cant/artwork/spate; all not allowed as shortcut now | Explicit canonical target field: NO | TOUCH_UI_DISPLAY_ONLY + NEEDS_OWNER_GO_FOR_PAYLOAD |
| Print required | Artwork section; face finish options | print_laminate/execution type, no separate boolean | `artworkPrintedArtwork`, `finishOracalPrintLamination` | PARTIAL | print policy visible partially | artwork confirm button exists | Required for quote visible | print_required as separate semantic decision | Separate boolean control: NO | TOUCH_UI_DISPLAY_ONLY + NEEDS_OWNER_GO_FOR_PAYLOAD |
| Lamination required | Artwork section; face finish options | print_laminate/execution type, no separate boolean | `artworkPrintedArtwork`, `finishOracalPrintLamination` | PARTIAL | lamination policy visible partially | artwork confirm button exists | Required for quote visible | lamination_required as separate semantic decision | Separate boolean control: NO | TOUCH_UI_DISPLAY_ONLY + NEEDS_OWNER_GO_FOR_PAYLOAD |
| Artwork / printed_artwork | `IntakeV6ArtworkFinishSection.tsx`, role table | role suggestion, artwork card, confirm artwork | `artworkPrintedArtwork` | YES | suggestion-not-final visible | Confirm artwork exists | Requires confirmation visible | choices should stay visible | NO | TOUCH_UI_DISPLAY_ONLY |
| Artwork-only decision | `IntakeV6ArtworkOnlyDecisionPanel.tsx` | artwork-only confirm/exclude when guard triggers | `artworkPrintedArtwork` | PARTIAL | policy visible through chip | operator confirm path exists conditionally | Required for quote when active | not always visible if guard inactive | NO for conditional path | LEAVE_UNCHANGED |
| Ignored decision | role table | ignore role option | `artworkPrintedArtwork` | PARTIAL | choice visible in chip | role confirmation path exists | Required before quote when relevant | Review not live-visible under blocker | NO | LEAVE_UNCHANGED |
| Lighting mode | `IntakeV6ReviewLightingSection.tsx` | LED toggle, system, color, wattage | `electricalLedCables` | YES | default/prefill visible partially | controls operator-editable | order/execution and conditional quote visible | commercial electrical scope quote condition can be clearer | NO | TOUCH_UI_DISPLAY_ONLY |
| LED settings | `IntakeV6ReviewLightingSection.tsx` | module wattage, derived counts, strip lengths | `electricalLedCables` | YES/PARTIAL | existing form value visible | controls operator-editable | order/execution visible | derived vs confirmed distinction can be clearer | NO | TOUCH_UI_DISPLAY_ONLY |
| Included default cables | `IntakeV6ReviewLightingSection.tsx` | no cable fields | `electricalLedCables` | YES as display | owner defaults visible | no cable confirmation control | order/execution visible | label should say defaults are commercial included, not planning payload | Cable fields: NO | TOUCH_UI_DISPLAY_ONLY |
| Extra cable/site details | no first-class Review control | no cable/site fields | `electricalLedCables` | PARTIAL | owner policy visible | no control | order/execution visible | missing UI gap should be explicit | YES | DOC_ONLY_GAP + TOUCH_UI_DISPLAY_ONLY |
| PSU / surse | lighting and mounting tab | PSU select/derived required watts | `electricalLedCables` | PARTIAL | existing form value visible | operator selectable | order/execution visible | placement policy missing | PSU placement control: NO | DOC_ONLY_GAP + TOUCH_UI_DISPLAY_ONLY |
| Support / bare | Review mounting tab | mounting_system steel/aluminum bars, bar profile | `supportBars` | PARTIAL | optional unless detected/suggested visible | operator can choose bars via mounting | conditional quote/order/execution visible | first-class support taxonomy missing | support_required/type/material/position: NO | DOC_ONLY_GAP + TOUCH_UI_DISPLAY_ONLY |
| Mounting scope | Review mounting tab | mounting system/template/bar profile | `mountingScope` | PARTIAL | no mounting/included/external/to decide visible as chip | operator edits mounting system | quote blocker when included/external visible | commercial scope control missing | included/external scope control: NO | DOC_ONLY_GAP + TOUCH_UI_DISPLAY_ONLY |
| Pricing / Cost boundary | mounting tab boundary chip; readiness panel copy | no pricing repair control | `pricingBoundary` | NOT_PRODUCT_TRUTH visible | boundary visible | n/a | internal-only visible | Product Truth first / pricing coverage after truth can be clearer | NO | TOUCH_UI_DISPLAY_ONLY |
| Quote / Order / Execution classification | all badge metadata | per-component blocker chips | all component question metadata | PARTIAL | owner-approved rules visible | n/a | required/conditional/internal labels visible | conditional quote/order-execution-only taxonomy needs helper support | NO | TOUCH_UI_DISPLAY_ONLY |

## Planned UI-only closure

- Normalize helper taxonomy with `MISSING_UI_GAP`, `QUOTE_BLOCKER_CONDITIONAL`, and `ORDER_EXECUTION_ONLY` display statuses.
- Extend existing chip metadata only; do not add controls.
- Keep `CONFIRMED_TRUTH` unused unless the UI state genuinely proves confirmation.
- Add targeted helper/component tests.

## Final decision matrix

| Row | Existing control | UI visibility after task | Product Truth candidate | Owner-approved default | Quote blocker | Order blocker | Execution blocker | Payload changed | Readiness changed | Next status |
|---|---|---|---|---|---|---|---|---|---|---|
| Face material | PARTIAL | PLANNED YES | YES | YES | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Face thickness | NO | PLANNED PARTIAL | YES | YES | YES | YES | YES | NO | NO | DOC_ONLY_GAP |
| Back Forex | YES | PLANNED YES | YES | YES | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Back sanfren | YES | PLANNED YES | YES | YES | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Return depth | YES | PLANNED YES | YES | PARTIAL | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Return color/RAL/finish | YES | PLANNED YES | YES | PARTIAL | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Oracal series | YES | PLANNED YES | YES | NO | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Oracal color | YES | PLANNED YES | YES | NO | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Print required | PARTIAL | PLANNED PARTIAL | YES | NO | YES | YES | YES | NO | NO | NEEDS_UI_GAP_SLICE |
| Lamination required | PARTIAL | PLANNED PARTIAL | YES | NO | YES | YES | YES | NO | NO | NEEDS_UI_GAP_SLICE |
| Finish target | PARTIAL | PLANNED PARTIAL | YES | NO | YES | YES | YES | NO | NO | NEEDS_UI_GAP_SLICE |
| Artwork printed_artwork | YES | PLANNED YES | YES | NO | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Artwork-only | PARTIAL | PLANNED PARTIAL | YES | NO | YES | YES | YES | NO | NO | NEEDS_UI_GAP_SLICE |
| Ignored | PARTIAL | PLANNED PARTIAL | YES | NO | YES | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Lighting mode | YES | PLANNED YES | YES | PARTIAL | CONDITIONAL | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Included cable defaults | NO | PLANNED YES | YES | YES | NO | YES | YES | NO | NO | READY_FOR_PAYLOAD_DESIGN_LATER |
| Extra cable/site details | NO | PLANNED PARTIAL | YES | NO | CONDITIONAL | YES | YES | NO | NO | DOC_ONLY_GAP |
| PSU placement | NO | PLANNED PARTIAL | YES | NO | CONDITIONAL | YES | YES | NO | NO | DOC_ONLY_GAP |
| Support/bars | PARTIAL | PLANNED PARTIAL | YES | NO | CONDITIONAL | YES | YES | NO | NO | NEEDS_UI_GAP_SLICE |
| Mounting scope | PARTIAL | PLANNED PARTIAL | YES | NO | YES | YES | YES | NO | NO | NEEDS_UI_GAP_SLICE |
| Pricing/Cost boundary | YES | PLANNED YES | NO | NO | NO | NO | NO | NO | NO | INTERNAL_ONLY |

## Worklog status

COMPLETE.

The detailed gap map above was created before code edits.

## Implementation summary

Changed display-only metadata only:

- extended `intakeV6ComponentQuestionDisplay.ts` with display statuses for `MISSING_UI_GAP`, `QUOTE_BLOCKER_CONDITIONAL`, and `ORDER_EXECUTION_ONLY`;
- clarified existing chips for face material/thickness, back Forex/no-sanfren, return/cant target and selectable finishes, finish targets, print/lamination separation, artwork target, electrical default cables, special electrical/site gaps, support taxonomy gaps, mounting commercial-scope gaps, and Product Truth/pricing boundary;
- reused existing `IntakeV6ComponentQuestionBadges` surfaces already embedded in Review sections;
- did not add new form controls, wizard steps, payload fields, readiness logic, API calls, backend code, pricing logic, quote/order/execution behavior, ProductDefinition, ProductAggregate, or ExecutionPlan.

## Validation

Focused Vitest:

```text
pnpm.cmd vitest run src/lib/intakeV6/intakeV6ComponentQuestionDisplay.test.ts src/components/workos/intake-v6/IntakeV6ComponentQuestionBadges.test.tsx src/components/workos/intake-v6/IntakeV6LetterGroupFinishesSection.test.tsx src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx src/components/workos/intake-v6/IntakeV6ReviewBackingSelect.test.tsx src/components/workos/intake-v6/IntakeV6ReviewLightingSection.test.tsx
```

Result:

```text
Test Files  6 passed (6)
Tests       39 passed (39)
```

Diagnostics:

- TypeScript/TSX diagnostics: PASS for touched helper and focused tests.

Boundary checks:

- helper has no API/fetch/payload/readiness/downstream mutation path;
- display labels do not introduce commercial hour/minute pricing copy;
- `CONFIRMED_TRUTH` remains unused for fallback/default/gap labels.

## Runtime read-only guardrail

Route checked:

```text
http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator
```

Observed:

- `LIVE / DB` visible;
- Product Truth remains `BLOCKED / NEEDS_CONFIRMATION`;
- CTA `Creează draft intern V6` remains disabled;
- visible copy says the blocker is Product Truth/layer role confirmation, not Pricing Registry;
- no visible commercial hour/minute pricing copy;
- no confirmation/unlock action was clicked.

Review Phase 2 gap-closure labels not live-verified because layer_roles_incomplete correctly blocks access. Covered by component/helper tests only.

## Forbidden scope confirmation

Confirmed:

- no backend changes;
- no DB/schema/seeds changes;
- no analyzer changes;
- no payload changes;
- no ProductTruth runtime changes;
- no readiness/unlock logic changes;
- no pricing behavior changes;
- no ProductDefinition changes;
- no ProductAggregate changes;
- no Task Graph or ExecutionPlan changes;
- no quote/order/execution creation;
- no Employee Mobile changes.