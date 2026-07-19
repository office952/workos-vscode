# COMPOSITION CORRECTION CHECKPOINT V2

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `1ad841b55bd7357db49a67728a28f6e0a2a07db9` (visually REJECTED)  
**Functional truth baseline:** `9f0efa0ce810ec0126ec6b3e1abe5d8d1e675602`  
**Mode:** Checkpoint before implementation — frontend composition only

---

## Pre-flight answers

### 1–4. Git

| Item | Value |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `1ad841b` |
| Working tree | Dirty — extensive foreign WIP |
| Foreign WIP | backend services/schemas/tests, PreOrder panels, architecture docs, segmented e2e artifacts, analyzer/buildAnalysisReport, productDefinitionPreview, etc. — **untouched** |

### 5. Files modified by rejected commit `1ad841b` (frontend)

- `IntakeV6ConfirmHandoffPanel.tsx`
- `IntakeV6ConfirmStep.test.tsx` / `IntakeV6ConfirmStep.tsx`
- `IntakeV6FinalConfigurationSummary.tsx`
- `IntakeV6LayersOperatorPanel.tsx`
- `IntakeV6LiveCalculationSummary.tsx`
- `IntakeV6ProductCompositionPanel.tsx` (+ test)
- `IntakeV6ReviewOperatorBlockerBanner.tsx` (+ test)
- `IntakeV6ReviewSaveFooter.tsx`
- `IntakeV6ReviewSectionShell.tsx`
- `IntakeV6ReviewStep.tsx`
- `intakeV6FinalConfirmationBlockers.ts`
- `intakeV6QuoteHandoffReadiness.ts`

### 6. ReviewStep responsibility map (before)

| Metric | Value |
|--------|--------|
| Line count | **~3739** |
| Role | Orchestrator + Montaj domain markup + diagnostic fetch/mount + tab panels + save/footer wiring + commercial adjustments |

**Responsibilities retained in step (target):** workspace state, finish save, tab state, focus jumps, composition confirm handler, layout composition.

**To extract / re-own for this correction:**

| Owner | Surface |
|-------|---------|
| Form region chrome | tabs + attention corner + connected panel body |
| Diagnostic drawer | FormSystem / Capture / Planner / binding — lazy, outside document scroll |
| Product header | already `IntakeV6ProductCompositionPanel` — collapse further |
| Scope | already `IntakeV6OfferScopeReviewSummary` — demote to chip |
| Pricing rail | already `IntakeV6LiveCalculationSummary` — copy only |
| Attention | `IntakeV6ReviewOperatorBlockerBanner` → corner control |

### 7. Major visible regions (ReviewStep render order today)

1. Analysis-blocked banner (conditional)
2. **ProductCompositionPanel** (full width, above grid)
3. Logo-only commercial guard (conditional)
4. Mobile price spine
5. Grid: left column
   - OfferScope card
   - OperatorBlockerBanner (full-width compact band)
   - ReviewTabNav (detached)
   - Tab panels (Finisaje / Iluminare / Montaj) with SectionShell titles
6. Grid: right column — LiveCalculationSummary + commercial disclosure
7. Page-level Cant message (rare)
8. **Diagnostic accordion inline** (FormSystem + Capture + Planner + ProductSystem binding + AI + artwork complexity…)
9. Save footer (via workspace footer stack outside file)

### 8. Warning surfaces

| Surface | Component / source |
|---------|-------------------|
| Attention band | `IntakeV6ReviewOperatorBlockerBanner` |
| Product badge / CTA | `IntakeV6ProductCompositionPanel` |
| Pricing gate copy | `shortenOperatorPricingBlocker` ← backend blocker via `intakeV6OfficialPricingBlockerMessage` |
| Footer next action + sticky | `IntakeV6OperatorWorkspaceFooter` + guidance |
| Footer issues drawer | same footer |
| Confirmare consolidated | `IntakeV6FinalConfigurationSummary` |
| Local Cant | letter group / return-cant message |
| System header | app chrome (out of Intake ownership) |

### 9. Composition-confirmation surfaces

1. Product CTA `intake-v6-confirm-product-composition`
2. Product status badge
3. Blocker banner issue/action
4. Pricing shortened gate
5. Footer “Următorul pas: Confirmă compoziția…”
6. Footer issues inventory item
7. Guidance progress “Compoziție produs”
8. Confirmare checklist item (later step)

**V2 keep:** local CTA + compact issue count + footer next action.

### 10. Pricing-confirmation surfaces

- Rail unavailable message (`IntakeV6LiveCalculationSummary`)
- Backend string in dry-run blockers:  
  `backend/services/intake_v6_priced_quote_dry_run_service.py` L375  
  `"Operatorul trebuie sa confirme compozitia produsului propusa de analyzer inainte de priced dry-run ready."`  
  → FE must neutralize to operator copy (no backend change).

### 11. Footer / status surfaces

- `IntakeV6OperatorWorkspaceFooter` (sticky summary, next action, issues drawer, continue)
- `IntakeV6ReviewSaveFooter` (autosave quiet)
- Guidance sticky title

### 12. Technical diagnostic surfaces (mounted in operator scroll today)

Inside `intake-v6-review-technical-details` accordion:

- `FormSystemBackboneAwarenessPanel`
- `FormSystemRuntimeCaptureReadModelPanel`
- `ProductTruthPromotionPlannerPanel`
- ProductSystem binding card
- `IntakeV6OperatorWorkSummaryTechnicalDetails`
- `IntakeV6AiSemanticAssistPanel`
- `IntakeV6ArtworkComplexityCard` (and more below in file)

Plus Confirmare collapsed “Recapitulare și diagnostic tehnic”.

### 13. Duplicated Iluminare fields — source

- **Removed in V1:** `renderSectionByKey("iluminare")` (generic contract renderer)
- **Still shows “generic-looking” fields:** `IntakeV6ReviewLightingSection` with `hideContractManagedFields={false}` renders Tip iluminare + PSU inside specialized section (correct single owner — but SectionShell + helper make it feel dual)
- Owner rejection of “after” may have been wrong capture earlier; V2 must prove with panel-only screenshot

### 14. Engineering helper text — source

`IntakeV6ReviewLightingSection.tsx` ~L283–285:

> Sursele pentru iluminarea literelor (nu alimentarea 220V a carcasei multi-panou).

Also Montaj readiness blurb, SectionShell descriptions, Product System link labels.

### 15. Exact analyzer / dry-run pricing sentence — source

| Layer | Location |
|-------|----------|
| Backend truth string | `backend/services/intake_v6_priced_quote_dry_run_service.py` (~L375) |
| FE read | `intakeV6OfficialPricingBlockerMessage` ← `pricing.blockers[0].message` |
| FE display | `shortenOperatorPricingBlocker` in `IntakeV6LiveCalculationSummary.tsx` |

**V2 operator copy (FE only):** `Preț disponibil după confirmarea produsului.`

### 16. Diagnostic panels in operator mode

Fetched eagerly in ReviewStep (`getIntakeV6RuntimeCaptureReadModel`, `getIntakeV6ProductTruthPromotionPlanner`) and mounted inside page accordion even when collapsed (DOM present).

**V2:** lazy drawer/sheet — fetch+mount only when opened; not in normal document scroll.

---

## Target first paint (1440×1000)

```
[ Produs compact row | CTA if needed ]     [ Scope chip ]
┌─ Form unit ─────────────────────────────────────────────┬ Pricing ┐
│ [Finisaje|Iluminare|Montaj]              [ ! 2 ]        │ compact │
│ ┌─ connected panel ───────────────────────────────────┐ │         │
│ │ active form decisions immediately                   │ │         │
│ └─────────────────────────────────────────────────────┘ │         │
└─────────────────────────────────────────────────────────┴─────────┘
[ Footer: next action · inventory · back/continue ]
[ Diagnostic: entry only — opens separate drawer ]
```

## Tracks A–K commitment

| Track | Action |
|-------|--------|
| A | Ultra-compact product row; details expand only when needed |
| B | Scope → one chip/line |
| C | Tabs + panel = one bordered form unit; no banner between |
| D | Attention corner chip; no full-width incomplete slab |
| E | Composition message only CTA + count + footer |
| F | Finisaje rows immediate; drop redundant Finisaje SectionShell title |
| G | One lighting owner; kill helper; valid after proof |
| H | Flatten Montaj; rename ACM label; kill Product System L1 links |
| I | Confirmare single readiness channel; truthful blocked/ready shots |
| J | Diagnostic drawer outside scroll; lazy mount |
| K | Extract FormRegion + DiagnosticDrawer; report line counts |

## Truth freeze

No backend / DB / analyzer / FinishSetup / pricing formulas / blocker counts / Montaj contracts / persistence changes.

## Acceptance screenshots plan

Before = rejected V1 pack / live baseline. After = this build. Matrix per TASK prompt § screenshots.

---

**Status:** CHECKPOINT COMPLETE — implementation may begin.
