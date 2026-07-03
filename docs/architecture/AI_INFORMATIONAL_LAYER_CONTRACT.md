# AI Informational Layer — WorkOS Architecture Contract

## Purpose

Define **AI as a transversal informational layer** across WorkOS — Intake, ProductSystem, website order forms, and chatbot — without making AI an operational decision-maker.

This document is the architectural source of truth. Runtime implementations must remain **contract-first** and **read-only** until owner-approved provider integration and confirmation flows exist.

## Official formula

```txt
Geometria calculează.
Regulile de business validează.
AI-ul interpretează și asistă.
Operatorul/clientul confirmă.
Sistemul persistă doar ce este confirmat.
```

## Core principle

```txt
AI-ul informează.
AI-ul sugerează.
AI-ul explică.
AI-ul structurează date neclare.
AI-ul NU decide final.
AI-ul NU calculează cantități finale.
AI-ul NU creează taskuri reale.
AI-ul NU modifică prețuri/materiale/producție fără confirmare.
```

## Shared contract (schema)

Canonical schema version: `ai_informational_suggestion_v1`

Location:

- `backend/schemas/ai_informational_layer.py`
- `backend/services/ai_informational_layer_service.py`

### Envelope

```json
{
  "schema_version": "ai_informational_suggestion_v1",
  "source_context": "intake_v4_svg_review",
  "suggestions": [],
  "confidence": 0.0,
  "requires_confirmation": true,
  "confirmed_by_user_id": null,
  "confirmed_at": null,
  "used_for_pricing": false,
  "used_for_production": false,
  "used_for_task_generation": false,
  "writes_business_state": false,
  "warnings": []
}
```

### Source contexts

| Context | Purpose |
|---------|---------|
| `intake_v4_svg_review` | SVG semantic assist during operator review |
| `website_chatbot` | Public chat pre-intake collection |
| `website_order_form` | Guided client order form assist |
| `work_intake_internal` | Internal operator intake assistant |
| `product_template_assist` | Template recommendation assist |

### Suggestion categories

```txt
semantic_classification
missing_information
template_recommendation
client_intake_summary
production_risk_hint
material_intent_hint
file_quality_hint
question_suggestion
operator_explanation
```

### Boundary flags (every suggestion)

```json
{
  "is_ai_suggestion": true,
  "informational_only": true,
  "requires_operator_confirmation": true,
  "used_for_pricing": false,
  "used_for_production": false,
  "used_for_task_generation": false,
  "can_create_order": false,
  "can_create_execution_tasks": false
}
```

Envelope-level guard: `writes_business_state: false` until explicit confirmation build.

## Where AI will help

### 1. Intake V4 / SVG semantic assist (implemented as read-only preview)

AI may suggest:

- group appears to be letters / logo / artwork
- probable text label (never auto-applied)
- inner holes vs letter pieces (informational)
- file quality warnings (curves, incomplete layers)

Does **not** change: `letter_count`, perimeters, materials, tasks, quote, order, production.

Endpoint (Intake V4):

```txt
GET /api/v1/intake-v4/workspaces/{workspace_id}/ai-informational-assist-candidate
```

Legacy alias (semantic-only shape):

```txt
GET /api/v1/intake-v4/workspaces/{workspace_id}/ai-semantic-classification-candidate
```

### 2. Website order forms (future)

AI helps the client complete:

- product intent (volumetric letters, casetă, print, colantare)
- illuminated vs non-illuminated
- interior/exterior mount
- approximate dimensions
- logo/vector availability
- location photo context

Draft payload enters WorkOS as:

```txt
source = ai_assisted_client_draft
status = needs_operator_review
used_for_quote = false
```

### 3. Website chatbot (future)

AI acts as request intake assistant:

- collects fields and files
- identifies missing information
- asks clarifying questions
- proposes possible template (informational)
- produces request summary

Does **not** create final quote or order.

### 4. Work Intake internal assistant (future)

AI helps operators:

- summarize client request
- identify missing inputs
- propose next step
- explain blockers (`BLK-*`, readiness)
- draft client follow-up questions

### 5. ProductSystem / template recommendation (future)

AI may suggest:

- `TPL-VOLUMETRIC-LETTERS`
- illuminated box / print / wrap templates
- confidence + reasons

Final template activation remains **operator-confirmed**.

## Confirmation model (future persistence)

Only confirmed values may be written to business state:

| Field | Description |
|-------|-------------|
| `suggestion_id` | Stable suggestion reference |
| `source_context` | Where suggestion originated |
| `category` | Suggestion category |
| `accepted_suggestion` | Operator/client accepted AI hint |
| `confirmed_value` | Final confirmed semantic/value |
| `confirmed_at` / `confirmed_by_user_id` | Audit trail |

Status in current build: `not_persisted`.

## Allowed vs forbidden

### Low risk / informational (allowed as suggestions)

- Text/logo/artwork hints
- Client request summary
- Clarifying questions
- Missing field detection
- Probable template hint
- Operator explanations
- Incomplete file warnings
- Visual semantic grouping hints

### Medium risk — explicit confirmation required

- Final template choice
- Client requirement → exact product mapping
- Piece-to-character mapping
- Ambiguous logo vs text resolution
- Material/finish recommendation
- Operation recommendations

### Forbidden without confirmation

- Final price
- Final material quantity
- Final perimeter / letter_count
- Task activation
- Quote creation / acceptance
- Order creation
- ExecutionPlan / `tasks_json`
- Stock consumption
- Supplier selection
- Final delivery date

## What is NOT implemented yet

- External AI provider calls / API keys
- Operator or client confirmation persistence
- Website chatbot runtime
- Website order form AI runtime
- Writing AI suggestions into quote/pricing/material/tasks
- PNG/render preview tokens for vision models
- ProductSystem auto-activation from AI

## Implementation map (current)

| Layer | File |
|-------|------|
| Shared schema | `backend/schemas/ai_informational_layer.py` |
| Shared service | `backend/services/ai_informational_layer_service.py` |
| Intake V4 adapter | `backend/services/intake_v4_ai_semantic_classification_service.py` |
| Intake V4 endpoint | `backend/routers/intake_v4_workspaces.py` |
| Frontend panel | `frontend/src/components/workos/intake-v4/IntakeV4AiSemanticAssistPanel.tsx` |

## Related QA build

See `docs/qa/BUILD_INTAKE_V4_AI_INFORMATIONAL_LAYER_CONTRACT.md` for test evidence and file list.
