# ModuleDetectionResult — Step 1 Contract

**Status:** Foundation v1 (frontend-only)  
**Schema:** `module_detection_result_v1`  
**Related:** [WORKOS_INTAKE_TO_EXECUTION_OPERATING_MODEL.md](./WORKOS_INTAKE_TO_EXECUTION_OPERATING_MODEL.md)

---

## Purpose

`ModuleDetectionResult` is the **formal Step 1 output** between:

| Producer | Consumer |
|----------|----------|
| SVG analyzer (`analyzeSvgString` → `SvgAnalysisCoreReport`) | Operator confirmation UI |
| Future AI interpreter (informational suggestions only) | Future Product Form System |
| | Future Template Recommendation Engine |

It is the **detection contract**. It does **not** create downstream business artifacts.

---

## What it represents

- Parsed SVG layers with auto-detected roles, paint evidence, and geometry summaries
- High-level **detected modules** (e.g. volumetric letters, printed artwork) inferred from layers
- Role candidates per layer (from `guessLayerAutoRole` / `autoRoleCandidates`)
- Document- and detection-level warnings
- Step 1 blockers (e.g. artwork-only requires operator decision)
- Placeholders for future form/template recommendations (empty arrays today)
- Whether **operator confirmation** is still required before Step 2

---

## What it does NOT represent

| Excluded | Reason |
|----------|--------|
| `ProductDefinition` | Built at quote time from confirmed modules + template rules |
| Cost / pricing | Cost Engine + QuoteOrchestrator authority |
| Quote / order / execution | Step 3 handoff only after operator confirms |
| Confirmed layer roles as truth | Operator must confirm; contract carries **auto** roles + candidates |
| UI-only display state | Chips, KPI labels, polish — not in contract |
| Parts / nesting / sheet quote | Analyzer internals; unstable for Step 1 contract |
| Bond casetare defaults (`returnDepthMm`, etc.) | Operator Step 2 inputs, not detection |

---

## Rule: SVG/AI proposes, operator confirms

- `auto_role` and `detected_modules[]` are **suggestions**
- `requires_operator_confirmation: true` until `layerRoleConfirmation.confirmationStatus === "complete"` and artwork-only guard passes
- Future AI may populate `recommended_forms[]` / `recommended_templates[]` — AI **never** decides; operator confirms

---

## Schema (v1)

```typescript
ModuleDetectionResult {
  schema_version: "module_detection_result_v1"
  source: "svg_analyzer" | "ai_interpreter" | "combined"
  analysis_hash?: string          // client file hash when provided
  source_file_name?: string
  detected_layers: DetectedLayer[]
  detected_modules: DetectedModule[]
  role_candidates: RoleCandidateEntry[]
  warnings: ModuleDetectionWarning[]
  blockers: ModuleDetectionBlocker[]
  recommended_forms: []           // Product Form System — not implemented
  recommended_templates: []         // Template Recommendation — not implemented
  requires_operator_confirmation: boolean
  raw_analyzer_summary?: { ... }   // compatibility bridge only
}
```

---

## Mapper

**File:** `frontend/src/lib/intakeV6/mapAnalyzerReportToModuleDetectionResult.ts`

| | |
|--|--|
| **Input** | `SvgAnalysisCoreReport` (+ optional `analysisHash`, `layerRoleConfirmation` override) |
| **Output** | `ModuleDetectionResult` |
| **Side effects** | None |
| **Dependencies** | `intakeV6ArtworkOnlyGuard` for artwork-only blockers; layer helpers from analyzer |

Not wired as UI source of truth in v1 — available for adapters, persistence, and future Form System.

---

## Field mapping from analyzer

| ModuleDetectionResult | Source |
|-----------------------|--------|
| `detected_layers[]` | `report.layers` + `layerHasLetterPathGeometry` / `layerIsArtworkCandidate` |
| `detected_modules[]` | Inferred from layer roles + geometry; **no** volumetric module when artwork-only |
| `role_candidates[]` | `layer.autoRoleCandidates` |
| `warnings[]` | `report.warnings` |
| `blockers[]` | `resolveArtworkOnlyFatalBlockers` |
| `analysis_hash` | Caller-provided (typically `svg_source.file_hash`) |
| `raw_analyzer_summary` | `schemaVersion`, `engineVersion`, `confirmationStatus`, etc. |

---

## Intentionally not contracted (gaps)

| Gap | Notes |
|-----|-------|
| Product Form fragments | Awaits Product Form System contract |
| Template ranking / scores | Awaits Template Recommendation Engine |
| AI informational layer | Awaits interpreter; use `source: "combined"` later |
| Layer Semantic Registry canonical IDs | Names stable; registry IDs future work |
| `parts` / `nesting` / benchmark | Analyzer internals; may change without contract bump |
| Operator bond depth fields | Step 2 `finish_setup`, not Step 1 |

---

## Regression fixtures (controlled matrix)

| Fixture | Expected |
|---------|----------|
| `regression-v6-1layer-letters.svg` | `volumetric_letters` module, letter layers |
| `pbl.svg` | Multiple letter source layers |
| `pbl-layere.svg` | Letters + `printed_artwork`, no `unassigned` |
| `regression-v6-policromie-only.svg` | Artwork-only blocker, no false letter module |
| `pbl-complex.svg` | Out of scope |

Tests: `frontend/src/lib/intakeV6/moduleDetectionResult.test.ts`

---

## Next recommended step

1. **Product Form System contract** — map confirmed modules → form fragments  
2. Or **Layer Semantic Registry** if canonical layer/module IDs needed before forms
