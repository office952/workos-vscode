# BUILD_INTAKE_V4_AI_ASSISTED_SEMANTIC_CLASSIFICATION_CONTRACT

## Purpose

Prepare a **read-only contract** for AI-assisted semantic classification in Intake V4 / `TPL-VOLUMETRIC-LETTERS`. This build defines what we would send to an AI provider, what JSON we accept back as **suggestion only**, how an operator would confirm/correct semantics later, and strict safety boundaries.

**Principle:** Geometry calculates. AI interprets. Operator confirms.

## Why AI is a helper, not a decider

- Letter counts, perimeters, material quantities, nesting, task activation, and quote totals must remain **geometry- and operator-role-driven**.
- AI may help label ambiguous SVG groups (letters vs logo vs artwork) and suggest readable text when paths are curve-converted.
- AI output is **never** written to quote, pricing input, material breakdown, task dry-run, ExecutionPlan, or production handoff in this build.

## Data sent to AI (candidate payload)

Endpoint builds `IntakeV4AiSemanticClassificationCandidatePayload`:

| Field | Source |
|-------|--------|
| `workspace_id`, `template_id` | Workspace record |
| `source_file_type` | `"svg"` |
| `render_preview` | Contract placeholder; `available=false` until PNG preview pipeline exists |
| `groups[]` | One entry per layer from return-metric audit |
| `groups[].geometry` | Outer contours, inner holes, perimeters, area from SVG analysis + classification |
| `groups[].current_system_classification` | Derived from confirmed operator layer role (face / printed_artwork / …) |
| **Not included** | Invented text, quote geometry overrides, pricing fields |

## Accepted AI response (mock in this build)

Schema: `ai_semantic_classification_suggestion_v1`

Allowed `suggested_kind`:

- `letters`
- `logo_or_emblem`
- `artwork`
- `shape_symbol`
- `mixed`
- `unknown`

Each suggestion carries:

- `confidence`, `reasons`, `requires_operator_confirmation=true`
- `suggested_text=null` in mock (no OCR / filename guessing)
- Per-suggestion `boundary_flags`

## Safety boundary flags

All AI outputs include:

```json
{
  "is_ai_suggestion": true,
  "requires_operator_confirmation": true,
  "used_for_pricing": false,
  "used_for_production": false,
  "used_for_task_generation": false
}
```

## Permitted (safe / low risk)

- Suggested group kind (letters / logo / artwork)
- Suggested display label (`emblem`, `artwork`)
- Warnings (e.g. text converted to curves)
- Visual grouping hints for operator review

## Medium risk — confirmation required (future)

- Mapping contours to individual characters
- Logo vs letter disambiguation on ambiguous shapes
- Multi-element group suggestions

## Forbidden without operator confirmation

- Final `letter_count`
- Material quantities / perimeters overrides
- Nesting placements
- Task activation / ExecutionPlan / `tasks_json`
- Quote price / order handoff / stock consumption

## Operator confirmation model (contract only)

`IntakeV4OperatorSemanticConfirmationContract` documents future fields:

- `group_id`, `accepted_suggestion`, `confirmed_kind`, `confirmed_text`
- `operator_notes`, `ai_confidence_at_confirmation`
- `confirmed_at`, `confirmed_by_user_id`

Status: `not_persisted` — no PUT/POST confirmation endpoint in this build.

## What this build does NOT affect

- Material breakdown quantities
- Pricing input preview / quote creation
- Production task dry-run / task generation dry-run
- Layer role confirmation persistence
- Finish setup / commercial spine
- V2 / V3 intake paths

## Endpoint

```
GET /api/v1/intake-v4/workspaces/{workspace_id}/ai-semantic-classification-candidate
```

Response:

```json
{
  "preview_only": true,
  "ai_not_called": true,
  "candidate_payload": { "...": "..." },
  "mock_suggestion": { "...": "..." },
  "boundary_flags": { "...": "..." },
  "operator_confirmation_contract": { "...": "..." }
}
```

Service: `backend/services/intake_v4_ai_semantic_classification_service.py`

## UI (minimal)

Review Step panel: **AI semantic assist — sugestii viitoare** (collapsible)

- Shows `AI not connected yet`, candidate ready, mock suggestions per layer
- Banner: *AI suggestion only — not used for pricing or production until confirmed.*

## Files changed

| Area | File |
|------|------|
| Schemas | `backend/schemas/intake_v4.py` |
| Service | `backend/services/intake_v4_ai_semantic_classification_service.py` |
| Workspace wrapper | `backend/services/intake_v4_workspace_service.py` |
| Router | `backend/routers/intake_v4_workspaces.py` |
| Tests | `backend/tests/test_intake_v4_ai_semantic_classification_contract.py` |
| Frontend API | `frontend/src/lib/intakeV4/intakeV4Api.ts` |
| Frontend panel | `frontend/src/components/workos/intake-v4/IntakeV4AiSemanticAssistPanel.tsx` |
| Review Step | `frontend/src/components/workos/intake-v4/steps/IntakeV4ReviewStep.tsx` |

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_ai_semantic_classification_contract.py -q
```

(Results recorded below after run.)

**Result:** `8 passed` in `tests/test_intake_v4_ai_semantic_classification_contract.py`

## Boundary

- No runtime AI dependency, API keys, or external HTTP calls
- No writes to quote / tasks / material / pricing from AI suggestions
- No ExecutionPlan or real task creation

## Next build candidates

1. **Operator confirmation UI + persistence** — store `operator_confirmed_semantics` on workspace payload
2. **Safe AI provider integration** — owner-approved provider, redacted candidate payload, audit log
3. **Render preview tokens** — PNG/crop upload for vision models without exposing local paths in API
