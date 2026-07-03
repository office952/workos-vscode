# BUILD_AI_KNOWLEDGE_AND_ADVISORY_LAYER_STRATEGY_AUDIT

## Purpose

Strategic audit (documentation only) extending the implemented **AI Informational Layer** into a full **AI Knowledge & Advisory Layer** theory for WorkOS — website, chatbot, order forms, JPEG pre-estimate, ProductSystem templates, and operator copilot — without runtime implementation.

**Verdict:** **PASS (strategy audit complete — no runtime code)**

## Context

- Existing foundation: commit `ba0c8ab` — `feat(intake-v4): add AI Informational Layer read-only contract`
- Architecture baseline: `docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md`
- This audit answers the 10 strategic questions and defines 13 conceptual modules

## Branch / HEAD

| Item | Value |
|------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD at audit start | `ba0c8ab` |
| Commit/push | **Not performed** (docs only, awaiting owner confirmation) |

## Files created

| File | Role |
|------|------|
| `docs/architecture/AI_KNOWLEDGE_AND_ADVISORY_LAYER_STRATEGY.md` | Full strategy architecture |
| `docs/qa/BUILD_AI_KNOWLEDGE_AND_ADVISORY_LAYER_STRATEGY_AUDIT.md` | This QA audit record |

## Strategic questions answered

| # | Question | Answer summary |
|---|----------|----------------|
| 1 | Site theory & forms | **AI Site Theory Keeper** — drift detection between marketing copy, form fields, and active `TPL-*` matrix |
| 2 | Website chatbot | **AI Website Chatbot Assistant** — collect intent/files, missing info, template hints; handoff to operator |
| 3 | Client text → draft order | **AI Intake Assistant** + form assistant → `ai_assisted_client_draft` / `needs_operator_review` |
| 4 | JPEG analysis | **AI Image/JPEG PreQuote Estimator** — visual hypothesis only; not production file; disclaimers mandatory |
| 5 | Fabrication variants | **fabrication_variant** suggestions + Template Advisor ranking |
| 6 | Modify existing templates | **Template Gap Detector** — advisory gaps; owner applies via BUILD/playbook |
| 7 | Propose new templates | **Template Advisor** → `template_proposal` draft; owner onboarding required |
| 8 | Incomplete template signal | Gap detector compares dossier ↔ intake ↔ geometry ↔ QA docs |
| 9 | Prevent code/logic errors | **Consistency Reviewer** — non-blocking CI narrative; pytest remains truth |
| 10 | Link to Quote/Order/Production | Advisory envelopes stop at confirmation; geometry/rules/pricing unchanged |

## Modules defined (13)

1. AI Site Theory Keeper  
2. AI Intake Assistant  
3. AI Website Chatbot Assistant  
4. AI Website Order Form Assistant  
5. AI Image/JPEG PreQuote Estimator  
6. AI SVG Semantic Assistant *(partial — read-only contract exists)*  
7. AI Template Advisor  
8. AI Template Gap Detector  
9. AI ProductSystem Advisor  
10. AI Missing Info Assistant  
11. AI Consistency Reviewer  
12. AI Client Explanation Assistant  
13. AI Operator Copilot  

Each module documented in strategy doc with: Purpose, Input, Output, Allowed, Forbidden, Confirmation, Integration, Risks, Safe MVP, Future.

## Website chatbot — how AI helps

- Conversational collection of product intent, dimensions (approximate), mounting, illumination, files  
- Produces advisory envelope: summary, missing fields, template **candidates** (not selection)  
- Explicit: no final price, no order creation  
- Session ends in operator-reviewed Work Intake draft  

## Website order form — how AI helps

- Field-level guidance aligned with site theory  
- Validates completeness against template required-field contract  
- Submit → draft payload with `used_for_quote=false` until operator review  
- Supports Rough Estimate eligibility flag (informational only)  

## ProductSystem templates — how AI helps

- **Template Advisor:** rank `TPL-*` from client intent  
- **Gap Detector:** find missing quote_input keys, metric ambiguities, doc drift  
- **ProductSystem Advisor:** explain operations/materials/readiness in operator language  
- Activation remains **owner playbook PASS** — AI never activates  

## New template proposals — how AI helps

- Proposes draft template code (e.g. `TPL-LIGHTBOX-ACM-FACE-PLEXI`) with suggested fields, materials, operations  
- Status: `proposal_draft` — not in production registry until onboarding BUILD completes  
- Cross-check against playbook sections 3–29  

## Code/logic error prevention — how AI helps

- Non-blocking advisory on doc/test drift, metric naming consistency, blocker coverage  
- Explains pytest/BUILD failures in plain language  
- Does **not** auto-fix, auto-merge, or bypass CostEngine/Pricing Registry  

## Quote statuses

| Status | AI role | Pricing | Confirmation |
|--------|---------|---------|--------------|
| **Rough Estimate** | Eligibility + questions | Disallowed (`used_for_pricing=false`) | Client + operator |
| **PreQuote** | Blocker explanations | CostEngine after operator confirms inputs | Operator |
| **Final Quote** | Excluded from computation | Deterministic engines only | Existing commercial gates |

## Safety gates

Common flags documented in strategy doc — aligned with `AiInformationalBoundaryFlags` in `backend/schemas/ai_informational_layer.py`.

Post-confirmation promotion paths documented — none auto-write to ExecutionPlan, orders, or final quote.

## Forbidden list (explicit)

Documented in strategy doc — includes quote final, order, ExecutionPlan, `tasks_json`, stock, CostEngine, pricing registry, template production activation.

## What is NOT implemented

```txt
- No new runtime services beyond existing Intake V4 AI read-only endpoint
- No website chatbot/order form APIs
- No JPEG vision pipeline
- No site theory automation
- No template proposal persistence
- No AI provider integration
- No commits in this audit build (pending owner)
```

## Tests run

**None** — documentation-only audit. No code changed.

## Boundary

- No runtime AI dependency  
- No API keys  
- No CostEngine / Pricing Registry / ExecutionPlan changes  
- No modification to letter classification or nesting builds in progress  

## Recommended next build

**Priority 1:** `BUILD_AI_OPERATOR_SEMANTIC_CONFIRMATION_PERSISTENCE` — close Intake V4 SVG loop with confirmed semantics storage.

**Priority 2:** `BUILD_AI_SITE_THEORY_KEEPER_MVP` — read-only drift report (site copy vs active templates).

**Priority 3:** `BUILD_AI_WEBSITE_ORDER_FORM_DRAFT_CONTRACT` — public draft payload + `needs_operator_review` API shell (no AI provider yet).

## Commit recommendation

**Optional — docs-only commit when owner confirms:**

```txt
docs(architecture): add AI Knowledge and Advisory Layer strategy audit
```

Separate from:

- `ba0c8ab` AI Informational Layer (already committed)  
- Pending `BUILD_INTAKE_V4_LETTER_PART_HOLE_CLASSIFICATION_FIX` (uncommitted code)  

**Do not push** until owner approves.

## Commands

None required for this audit.

## Related

- `docs/architecture/AI_KNOWLEDGE_AND_ADVISORY_LAYER_STRATEGY.md`
- `docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md`
- `docs/qa/BUILD_INTAKE_V4_AI_INFORMATIONAL_LAYER_CONTRACT.md`
