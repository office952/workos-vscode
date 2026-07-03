# AI Knowledge & Advisory Layer — WorkOS Strategy

## Purpose

Extend the existing **AI Informational Layer** (`ai_informational_suggestion_v1`) into a transversal **AI Knowledge & Advisory Layer** for WorkOS — a read-only, contract-first advisory surface that informs, explains, proposes, structures unclear data, and maintains coherence across website theory, intake, ProductSystem templates, quotes, and production handoff — **without becoming an operational decider**.

This document is **strategy and architecture only**. No runtime AI provider, no business writes, no pricing/production side effects.

**Foundation already in repo:**

- `docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md`
- `backend/schemas/ai_informational_layer.py`
- Intake V4 SVG read-only preview endpoint

---

## Official formula

```txt
Geometria calculează.
Business rules validează.
AI interpretează și consiliază.
Operatorul/clientul confirmă.
Sistemul persistă doar ce este confirmat.
```

## Core principle

```txt
AI-ul informează.
AI-ul explică.
AI-ul propune.
AI-ul structurează date neclare.
AI-ul semnalează riscuri și lipsuri.
AI-ul ajută la menținerea teoriei site-ului și a template-urilor.
AI-ul NU decide final.
AI-ul NU modifică prețuri finale.
AI-ul NU creează taskuri reale.
AI-ul NU creează comenzi fără confirmare.
AI-ul NU scrie business state operațional fără confirmare.
```

---

## Architecture overview

```txt
┌─────────────────────────────────────────────────────────────────────────┐
│                     AI Knowledge & Advisory Layer                        │
│  (informational envelopes, suggestion categories, boundary flags)        │
└─────────────────────────────────────────────────────────────────────────┘
         │              │              │              │              │
         ▼              ▼              ▼              ▼              ▼
   Site Theory    Website        Work Intake     ProductSystem    Intake V4
   Keeper         Chatbot/       Internal        Template         Geometry/
                  Order Form     Copilot         Advisor          SVG Assist
         │              │              │              │              │
         └──────────────┴──────────────┴──────────────┴──────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
           Confirmed facts only              Operational truth
           (operator/client)                  (geometry, rules, registry)
                    │                               │
                    ▼                               ▼
              Draft payloads                 Quote / Order / Production
              PreQuote / Rough Estimate        (existing WorkOS gates)
```

### Layering model

| Layer | Role | Source of truth |
|-------|------|-----------------|
| **Geometry engine** | Perimeters, counts, nesting footprints | SVG analysis + classification services |
| **Business rules** | Readiness, blockers, template contracts | pytest, BUILD docs, ProductSystem dossier |
| **Pricing / CostEngine** | Final commercial totals | Pricing Registry + owner-confirmed rates |
| **AI Advisory** | Interpretation, gaps, drafts, explanations | Suggestions only — never final |
| **Human confirmation** | Persisted operational facts | Operator / owner / client review |

### Shared envelope (extends existing contract)

Proposed schema version: `ai_advisory_envelope_v1` (superset of `ai_informational_suggestion_v1`)

```json
{
  "schema_version": "ai_advisory_envelope_v1",
  "module": "ai_website_chatbot_assistant",
  "source_context": "website_chatbot",
  "knowledge_refs": ["site_theory:volumetric_letters_v1", "tpl:TPL-VOLUMETRIC-LETTERS"],
  "suggestions": [],
  "draft_artifacts": [],
  "confidence": 0.0,
  "requires_confirmation": true,
  "quote_eligibility": "none",
  "boundary_flags": {
    "is_ai_suggestion": true,
    "informational_only": true,
    "requires_confirmation": true,
    "used_for_pricing": false,
    "used_for_production": false,
    "used_for_task_generation": false,
    "writes_business_state": false
  }
}
```

New `source_context` values (future):

```txt
site_theory_review
website_chatbot
website_order_form
work_intake_internal
intake_v4_svg_review
product_template_assist
template_gap_review
jpeg_prequote_estimate
code_consistency_review
```

New suggestion categories (extends existing list):

```txt
site_theory_drift
fabrication_variant
template_gap
template_proposal
rough_estimate_eligibility
jpeg_visual_interpretation
consistency_warning
code_smell_hint
```

---

## Conceptual modules

Each module produces **advisory envelopes only**. Integration points reference existing WorkOS boundaries (Intake V4, Work Intake, ProductSystem registry, QuoteWizard guards).

---

### 1. AI Site Theory Keeper

| Field | Value |
|-------|-------|
| **Purpose** | Maintain coherence between public website copy, order form fields, chatbot scripts, and actual ProductSystem capabilities |
| **Input** | Site content snapshots, form schema JSON, template registry metadata, BUILD/QA docs, known blockers |
| **Output** | Drift reports, missing FAQ entries, field-to-template mapping suggestions |
| **Allowed** | Flag outdated claims; suggest copy fixes; map “firmă luminoasă” → candidate templates |
| **Forbidden** | Publish site changes; activate templates; change pricing copy to final numbers |
| **Confirmation** | Marketing/owner approves copy and form schema changes |
| **Plugs into** | CMS / static site repo; form builder config; ProductSystem template list (read-only) |
| **Risks** | Website promises product not wired in WorkOS |
| **Safe MVP** | Read-only diff: site claims vs `TPL-*` activation matrix |
| **Future** | Automated PR suggestions on marketing repo |

---

### 2. AI Intake Assistant

| Field | Value |
|-------|-------|
| **Purpose** | Help operators structure incoming requests into reviewable intake drafts |
| **Input** | Email/text attachments, client messages, partial Work Intake state |
| **Output** | `client_intake_summary`, `missing_information`, `question_suggestion` items |
| **Allowed** | Summarize; list missing vector/dimensions/mounting; propose next step |
| **Forbidden** | Create quote; set template as active; write geometry metrics |
| **Confirmation** | Operator opens/reviews Work Intake workspace |
| **Plugs into** | Work Intake V2/V4 workspace creation (draft payload only) |
| **Risks** | Wrong product family pre-selected |
| **Safe MVP** | Internal panel: paste client text → draft summary JSON |
| **Future** | Email ingress → draft Work Intake with `needs_operator_review` |

---

### 3. AI Website Chatbot Assistant

| Field | Value |
|-------|-------|
| **Purpose** | Public-facing conversational pre-intake — collect intent, files, constraints |
| **Input** | Chat turns, uploaded files (metadata only in MVP), site theory pack |
| **Output** | Structured request summary, missing fields, template candidates (informational) |
| **Allowed** | Clarifying questions; explain what files are needed; rough product family hint |
| **Forbidden** | Final price; order creation; “your quote is X RON” |
| **Confirmation** | Handoff to operator; client submits form → `needs_operator_review` |
| **Plugs into** | Website widget → API `POST /public/ai-advisory/chat-turn` (future, read-only session) |
| **Risks** | Overconfident fabrication advice; GDPR/file handling |
| **Safe MVP** | Scripted + AI assist for question generation only; no quote numbers |
| **Future** | Session persistence with advisory envelope audit trail |

---

### 4. AI Website Order Form Assistant

| Field | Value |
|-------|-------|
| **Purpose** | Guide client through order form fields with contextual help |
| **Input** | Partial form state, field definitions, site theory, template catalog (read-only) |
| **Output** | Inline hints, validation explanations, draft payload on submit |
| **Allowed** | “For exterior illuminated letters we typically need…”; flag missing logo file |
| **Forbidden** | Auto-submit to quote; bypass operator review |
| **Confirmation** | Submit creates `ai_assisted_client_draft` / `needs_operator_review` |
| **Plugs into** | Public order form → Work Intake draft API |
| **Risks** | Client assumes submission = confirmed order |
| **Safe MVP** | Static field help + AI-generated clarifications (no pricing) |
| **Future** | Dynamic form branches from template candidates |

**Draft payload rule:**

```txt
source = ai_assisted_client_draft
status = needs_operator_review
used_for_quote = false
quote_eligibility = none | rough_estimate_only
```

---

### 5. AI Image/JPEG PreQuote Estimator

| Field | Value |
|-------|-------|
| **Purpose** | Interpret photos of existing signage for **orientative** guidance only |
| **Input** | JPEG/PNG, optional client notes, site theory |
| **Output** | Visual product hypothesis, file-quality warnings, missing production inputs |
| **Allowed** | “Appears volumetric / lightbox / flat print”; “not production file”; list needed assets |
| **Forbidden** | Final dimensions; final letter count; binding price |
| **Confirmation** | Operator validates; vector upload required for PreQuote+ |
| **Plugs into** | Website upload → advisory artifact attached to intake draft |
| **Risks** | Vision model hallucination on scale/material |
| **Safe MVP** | Category + disclaimer only; no numeric estimate |
| **Future** | Rough dimension band if reference object visible (low confidence, explicit band) |

---

### 6. AI SVG Semantic Assistant

| Field | Value |
|-------|-------|
| **Purpose** | Interpret SVG layer groups (letters, logo, artwork, holes) — **implemented read-only** |
| **Input** | Candidate payload from geometry audit (groups, roles, metrics) |
| **Output** | `semantic_classification`, `file_quality_hint` suggestions |
| **Allowed** | Suggest kind/text label (null until confirmed); curve-conversion warnings |
| **Forbidden** | Override `letter_count`, perimeters, material breakdown |
| **Confirmation** | Operator confirms per group (future build) |
| **Plugs into** | Intake V4 Review Step — `GET .../ai-informational-assist-candidate` |
| **Risks** | OCR-like guesses on outlined text |
| **Safe MVP** | **Done:** mock heuristic + contract |
| **Future** | Vision on PNG preview token + operator confirmation persistence |

---

### 7. AI Template Advisor

| Field | Value |
|-------|-------|
| **Purpose** | Recommend probable ProductSystem template from client intent + files |
| **Input** | Intake draft, advisory summaries, template registry metadata |
| **Output** | Ranked `template_recommendation` with confidence + reasons |
| **Allowed** | “Likely TPL-VOLUMETRIC-LETTERS because…” |
| **Forbidden** | Activate template; patch dossier; skip onboarding playbook |
| **Confirmation** | Operator selects template in intake binding step |
| **Plugs into** | Work Intake template picker; Intake V4 `product_binding` (human set) |
| **Risks** | Wrong template → wrong quote_input contract |
| **Safe MVP** | Read-only ranking from keyword + field rules + AI narrative |
| **Future** | Learn from historical operator corrections (audit only) |

---

### 8. AI Template Gap Detector

| Field | Value |
|-------|-------|
| **Purpose** | Compare template dossier, intake fields, geometry outputs, and QA docs for missing links |
| **Input** | Template dossier JSON, BUILD docs, pytest markers, sample workspace payloads |
| **Output** | `template_gap` report: missing quote_input keys, ambiguous metrics, undocumented blockers |
| **Allowed** | List gaps; cite doc/code references; suggest owner questions |
| **Forbidden** | Auto-fix dossier; activate partial template |
| **Confirmation** | Owner accepts gap backlog into BUILD roadmap |
| **Plugs into** | ProductSystem template registry; `docs/qa/BUILD_*`; architecture audits |
| **Risks** | False gaps from stale docs |
| **Safe MVP** | Static checklist runner + AI narrative for `TPL-VOLUMETRIC-LETTERS` |
| **Future** | CI advisory job on template PRs (non-blocking) |

---

### 9. AI ProductSystem Advisor

| Field | Value |
|-------|-------|
| **Purpose** | Help owners/operators understand template capabilities, operations, materials, handoff |
| **Input** | Template dossier, operation catalog, readiness model |
| **Output** | `operator_explanation`, `production_risk_hint` |
| **Allowed** | Explain what template supports; what blocks quote/order |
| **Forbidden** | Change CostEngine formulas; alter pricing registry |
| **Confirmation** | N/A for read-only explanations; yes for acting on recommendations |
| **Plugs into** | QuoteWizard help; Intake V4 readiness panels |
| **Risks** | Misexplaining blocker severity |
| **Safe MVP** | RAG over approved dossier + decisions log |
| **Future** | Cross-template comparison for sales |

---

### 10. AI Missing Info Assistant

| Field | Value |
|-------|-------|
| **Purpose** | Unified missing-field detection across chatbot, form, intake, quote readiness |
| **Input** | Partial payloads vs template required-field contract |
| **Output** | `missing_information`, prioritized questions |
| **Allowed** | “Need vector logo, approximate height, mounting surface photo” |
| **Forbidden** | Invent defaults for required commercial fields |
| **Confirmation** | Client/operator supplies values |
| **Plugs into** | All intake surfaces; `BLK-*` readiness codes |
| **Risks** | Annoying over-questioning |
| **Safe MVP** | Rule-based required fields + AI phrasing |
| **Future** | Context-aware priority by job value/urgency |

---

### 11. AI Consistency Reviewer

| Field | Value |
|-------|-------|
| **Purpose** | Cross-check client story vs files vs selected template vs geometry |
| **Input** | Chat summary, form answers, SVG analysis summary, template choice |
| **Output** | `consistency_warning` — contradictions and soft mismatches |
| **Allowed** | “Client said non-illuminated but form says LED”; “Artwork layer role face but described as print-only sticker” |
| **Forbidden** | Auto-correct template or finish |
| **Confirmation** | Operator resolves |
| **Plugs into** | Intake review step; pre-quote readiness |
| **Risks** | Noise on legitimate exceptions |
| **Safe MVP** | Deterministic rules + AI explanation |
| **Future** | Score readiness for PreQuote promotion |

---

### 12. AI Client Explanation Assistant

| Field | Value |
|-------|-------|
| **Purpose** | Generate client-safe explanations of process, delays, missing items |
| **Input** | Blockers, missing info, template-appropriate glossary |
| **Output** | Draft email/chat messages (informational) |
| **Allowed** | Plain-language “we need X because Y” |
| **Forbidden** | Promise delivery date; promise final price |
| **Confirmation** | Operator sends |
| **Plugs into** | CRM/email draft; chatbot suggested reply |
| **Risks** | Overpromising |
| **Safe MVP** | Template snippets + AI merge |
| **Future** | Multilingual client comms |

---

### 13. AI Operator Copilot

| Field | Value |
|-------|-------|
| **Purpose** | Internal assistant for next-best-action across WorkOS |
| **Input** | Workspace state, readiness, geometry summary, linked quote/order |
| **Output** | Next step, blocker explanation, draft client questions |
| **Allowed** | “Complete layer roles → confirm finish → pricing review” |
| **Forbidden** | Click-through automation of quote accept / order / task generation |
| **Confirmation** | Operator executes actions manually |
| **Plugs into** | Intake V4 operator workspace; QuoteWizard |
| **Risks** | Shortcutting safety gates |
| **Safe MVP** | Read-only copilot panel mirroring readiness API |
| **Future** | Guided workflows with explicit confirm cards |

---

## Mandatory production examples

### Example 1 — Client text

**Client writes:**

```txt
Vreau o firmă luminoasă cu logo și text pe perete, cam 3 metri, exterior.
```

**AI advisory draft (envelope):**

```json
{
  "module": "ai_website_chatbot_assistant",
  "source_context": "website_chatbot",
  "suggestions": [
    {
      "category": "client_intake_summary",
      "summary": "Exterior illuminated sign ~3m with logo + text on wall"
    },
    {
      "category": "template_recommendation",
      "payload": {
        "candidates": [
          {"template_code": "TPL-VOLUMETRIC-LETTERS", "confidence": 0.72, "reason": "illuminated + letters + logo"},
          {"template_code": "TPL-LIGHTBOX-ACM-FACE-PLEXI", "confidence": 0.45, "reason": "possible if single cabinet", "status": "not_active"}
        ]
      }
    },
    {
      "category": "missing_information",
      "reasons": ["vector logo", "exact width/height", "wall photo", "electrical access", "mounting height"]
    },
    {
      "category": "question_suggestion",
      "summary": "Este vorba de litere volumetrice individuale sau casetă luminoasă?"
    }
  ],
  "quote_eligibility": "rough_estimate_only",
  "boundary_flags": { "used_for_pricing": false, "writes_business_state": false }
}
```

**Operator path:** review → Work Intake draft → geometry when SVG available → PreQuote only after rules pass.

---

### Example 2 — JPEG image

**Client sends photo of existing sign.**

**AI advisory output:**

```txt
Visual hypothesis: volumetric illuminated letters (confidence: medium)
Not a production file — orientation/scale estimate only
Needs: vector PDF/SVG, measured dimensions, location install photo
Rough estimate eligibility: yes, with disclaimers — no final quote
Warnings: JPEG compression; unknown letter depth; material not verifiable from photo
```

**Forbidden:** “Exact price 12,400 RON” or “10 letters confirmed” from photo alone.

---

### Example 3 — Template gap (`TPL-VOLUMETRIC-LETTERS`)

**AI gap report:**

```txt
Observed geometry contract now distinguishes:
  real_letters_count vs volumetric_piece_count vs inner_holes_count
  letter_return_perimeter_ml vs led_perimeter_ml vs artwork_return_perimeter_ml

Gaps to document in dossier/intake UX:
  - artwork execution pending (needs_decision) vs active return
  - holes included in cant but excluded from letter_count
  - LED policy excludes holes and artwork by default

Recommendation: update template operator guide + site FAQ — not auto-change dossier
```

---

### Example 4 — New template proposal

**AI proposes (draft only):**

```txt
TPL-LIGHTBOX-ACM-FACE-PLEXI
Required fields: width_mm, height_mm, depth_mm, illumination, mounting, face_material, print_laminate
Materials: ACM, plexi face, vinyl print, LED strip, PSU
Operations: CNC sheet, print/laminate, assembly, electrical test
Owner must confirm: pricing registry rows, CostEngine handlers, intake zones, readiness blockers
Status: proposal_draft — NOT activatable until playbook PASS
```

---

## Quote status model

Three advisory/commercial tiers — AI may **suggest eligibility** only; promotion requires rules + human gates.

### Rough Estimate / Estimare orientativă

| Aspect | Rule |
|--------|------|
| **Allowed inputs** | Client text, JPEG, approximate dimensions, product family guess |
| **Confidence** | Low–medium; must show band/range or “TBD” |
| **Price format** | Range or “from X” with explicit disclaimer; never invoice-grade |
| **Disclaimers** | “Non-contractual”; “subject to vector survey”; “not production file” |
| **Blocks final quote** | No vector; no confirmed template; no geometry; owner policy |

### PreQuote / Ofertă tehnică preliminară

| Aspect | Rule |
|--------|------|
| **Allowed inputs** | Operator-reviewed intake; partial geometry; confirmed template candidate |
| **Confidence** | Medium; geometry-backed where available |
| **Price format** | Line items from CostEngine **after** operator confirms inputs — AI does not set totals |
| **Disclaimers** | “Preliminary”; “pending finish confirmation”; blockers listed |
| **Blocks final quote** | Unresolved `BLK-*`; pricing review incomplete; stale analysis hash |

### Final Quote / Ofertă finală

| Aspect | Rule |
|--------|------|
| **Allowed inputs** | Confirmed geometry, finish, template, registry prices, readiness PASS |
| **Confidence** | High — from deterministic engines, not AI |
| **Price format** | Commercial quote entity via existing guards |
| **Disclaimers** | Standard commercial terms only |
| **Blocks conversion** | N/A — this is the gate output |

**AI role per tier:**

```txt
Rough Estimate  → AI may suggest eligibility + questions only
PreQuote        → AI may explain blockers; operator confirms inputs
Final Quote     → AI excluded from price computation path
```

---

## Safety gates

### Common boundary flags (every advisory artifact)

```json
{
  "is_ai_suggestion": true,
  "informational_only": true,
  "requires_confirmation": true,
  "used_for_pricing": false,
  "used_for_production": false,
  "used_for_task_generation": false,
  "writes_business_state": false
}
```

Extended flags for advisory superset:

```json
{
  "can_create_order": false,
  "can_create_execution_tasks": false,
  "can_activate_template": false,
  "can_modify_pricing_registry": false,
  "can_modify_cost_engine": false,
  "quote_eligibility": "none"
}
```

### After confirmation — allowed promotions

| AI artifact | Confirmed becomes | Written by |
|-------------|-------------------|------------|
| Semantic suggestion | `operator_confirmed_semantic_fact` | Operator (future persistence) |
| Client chat draft | `work_intake_draft` reviewed | Operator |
| Template proposal | `product_system_template_draft` | Owner via playbook BUILD |
| Rough estimate | `preliminary_quote_marker` only | Operator + pricing guard |
| Site theory fix | Marketing/content PR | Owner/marketing |

**Never auto-promote** AI output to: Final Quote, Order, ExecutionPlan, `tasks_json`, inventory deduction.

---

## Forbidden without confirmation

```txt
- crea quote final
- accepta quote
- crea order
- crea ExecutionPlan
- scrie tasks_json
- consuma stoc
- decide materiale finale
- decide preț final
- decide termen final
- activa template nou în producție
- modifica registry de prețuri
- modifica CostEngine
- override geometry metrics (letter_count, perimeters, material qty)
```

---

## Linking AI to WorkOS domains (no-risk pattern)

```txt
Website / Chatbot / Form
  → advisory envelope + draft payload (needs_operator_review)
  → Work Intake workspace (human binding)

Intake V4 / Geometry
  → geometry services compute
  → AI reads candidate payload only
  → operator confirms semantics (future)

ProductSystem
  → AI reads dossier/registry (read-only)
  → gap detector + template advisor
  → owner activates via onboarding playbook

Quote
  → AI explains readiness/blockers
  → CostEngine/Pricing compute after confirmed inputs
  → Rough/PreQuote/Final gates unchanged

Order / Production
  → AI explains handoff blockers
  → task dry-run remains deterministic
  → no AI write to ExecutionPlan
```

---

## Preventing code/logic errors (without AI as decider)

AI **Consistency Reviewer** + **Template Gap Detector** assist engineering quality:

| Mechanism | AI role | Human role |
|-----------|---------|------------|
| pytest / BUILD docs | Surface doc/code drift narrative | Fix code or update docs |
| Template contract tests | Explain failure in plain language | Merge fix |
| Readiness `BLK-*` codes | Suggest missing BUILD coverage | Owner prioritizes |
| Cross-module metric names | Flag `letter_count` vs `real_letters_count` confusion | Align contract in BUILD |
| PR review (future) | Non-blocking advisory comment | Developer decides |

AI must **never** auto-merge, auto-activate template, or bypass CI. Advisory-only CI job: `ai_advisory_ci_report` (future).

---

## What is NOT implemented yet

```txt
- AI Knowledge & Advisory runtime services (except Intake V4 SVG read-only contract)
- Website chatbot / order form integration
- JPEG vision pipeline
- Site theory keeper automation
- Template proposal persistence
- Operator confirmation store
- Rough/PreQuote eligibility engine
- External AI provider wiring
- RAG over dossier with production API keys
```

---

## Recommended build sequence (future)

| Phase | Build | Delivers |
|-------|-------|----------|
| 1 | Operator semantic confirmation persistence | Close Intake V4 SVG loop |
| 2 | Site Theory Keeper MVP | Read-only drift report |
| 3 | Website order form draft API | `ai_assisted_client_draft` |
| 4 | Chatbot advisory API | Session envelopes, no pricing |
| 5 | Template Gap Detector CI | Non-blocking audit on `TPL-*` |
| 6 | JPEG PreQuote advisory | Vision + strict disclaimers |
| 7 | Template proposal workflow | Owner playbook integration |
| 8 | Owner-approved AI provider | Audit log + redaction |

---

## Related documents

- `docs/architecture/AI_INFORMATIONAL_LAYER_CONTRACT.md` — implemented foundation
- `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` — template activation discipline
- `docs/qa/BUILD_INTAKE_V4_AI_INFORMATIONAL_LAYER_CONTRACT.md` — Intake V4 AI commit evidence
