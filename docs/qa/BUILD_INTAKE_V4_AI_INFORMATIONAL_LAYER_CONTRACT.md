# BUILD_INTAKE_V4_AI_INFORMATIONAL_LAYER_CONTRACT

## Purpose

Extend Intake V4 AI assist into a **cross-cutting AI Informational Layer** foundation for WorkOS — not a narrow SVG-only feature. This build remains **contract-first** and **read-only** (no real AI provider, no business writes).

Architecture reference: [`docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md`](../architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md)

## Principle

```txt
Geometria calculează.
Regulile de business validează.
AI-ul interpretează și asistă.
Operatorul/clientul confirmă.
Sistemul persistă doar ce este confirmat.
```

## Delivered

1. Shared schema `ai_informational_suggestion_v1` — `backend/schemas/ai_informational_layer.py`
2. Shared service factories/adapters — `backend/services/ai_informational_layer_service.py`
3. Intake V4 SVG review adapter (candidate + mock suggestions)
4. Primary endpoint:

```txt
GET /api/v1/intake-v4/workspaces/{workspace_id}/ai-informational-assist-candidate
```

5. Legacy alias endpoint (semantic-only response shape):

```txt
GET /api/v1/intake-v4/workspaces/{workspace_id}/ai-semantic-classification-candidate
```

6. Expanded boundary flags (`informational_only`, `can_create_order`, `can_create_execution_tasks`, envelope `writes_business_state`)
7. Reusable suggestion categories + source contexts for future website chatbot / order forms
8. Minimal Review Step UI panel (informational only banner)
9. Architecture doc + this QA doc

## Response shape (primary endpoint)

```json
{
  "preview_only": true,
  "ai_not_called": true,
  "context": "intake_v4_svg_review",
  "candidate_payload": {},
  "mock_suggestions": [],
  "informational_envelope": {
    "schema_version": "ai_informational_suggestion_v1",
    "source_context": "intake_v4_svg_review",
    "writes_business_state": false
  },
  "boundary_flags": {
    "informational_only": true,
    "requires_operator_confirmation": true,
    "used_for_pricing": false,
    "used_for_production": false,
    "used_for_task_generation": false
  }
}
```

## Future surfaces (documented, not implemented)

| Surface | Future `source_context` | Entry status |
|---------|-------------------------|--------------|
| Website chatbot | `website_chatbot` | Schema ready |
| Website order form | `website_order_form` | Schema ready |
| Work Intake internal | `work_intake_internal` | Schema ready |
| ProductSystem assist | `product_template_assist` | Schema ready |

Client draft rule (future):

```txt
source = ai_assisted_client_draft
status = needs_operator_review
used_for_quote = false until confirmed
```

## What does NOT change

- Material breakdown
- Pricing input preview
- Production task dry-run
- Task generation dry-run / ExecutionPlan
- Quote / order / stock
- Layer roles / finish setup
- V2 / V3 paths

## Files changed

| Area | File |
|------|------|
| Architecture | `docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md` |
| Shared schema | `backend/schemas/ai_informational_layer.py` |
| Shared service | `backend/services/ai_informational_layer_service.py` |
| Intake V4 adapter | `backend/services/intake_v4_ai_semantic_classification_service.py` |
| Intake V4 schemas | `backend/schemas/intake_v4.py` |
| Workspace service | `backend/services/intake_v4_workspace_service.py` |
| Router | `backend/routers/intake_v4_workspaces.py` |
| Tests | `backend/tests/test_intake_v4_ai_informational_layer_contract.py` |
| Frontend API | `frontend/src/lib/intakeV4/intakeV4Api.ts` |
| Frontend panel | `frontend/src/components/workos/intake-v4/IntakeV4AiSemanticAssistPanel.tsx` |
| Review Step | `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` |

Prior QA doc `BUILD_INTAKE_V4_AI_ASSISTED_SEMANTIC_CLASSIFICATION_CONTRACT.md` superseded by this build for architectural scope.

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_ai_informational_layer_contract.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_ai_semantic_classification_contract.py -q
```

## Boundary

- No runtime AI dependency or API keys
- No external HTTP AI calls
- No writes to quote/pricing/material/tasks/production
- No ExecutionPlan / real tasks / stock consumption

## Next builds

1. Operator/client confirmation persistence (`ai_informational_confirmation_v1`)
2. Owner-approved AI provider integration with audit log
3. Website chatbot adapter implementing same envelope
4. Website order form draft intake adapter
5. PNG preview tokens for vision-assisted SVG review
