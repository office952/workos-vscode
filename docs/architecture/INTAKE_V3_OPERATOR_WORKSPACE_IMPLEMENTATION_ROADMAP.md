# Intake V3 Operator Workspace — Implementation Roadmap

**Date:** 2026-06-19  
**Type:** Architecture roadmap / phased build plan — **documentation only**  
**Repo:** `C:\Users\offic\workos`  
**Audience:** Product owner, Cursor agents, frontend/backend developers  
**Status:** Faza 0 complete — contract lock for subsequent builds

**Primary sources (read before any build):**

| Document | Path | Status |
|----------|------|--------|
| V2 vs V3 presentation audit | `docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md` | ✅ present |
| V3 architecture contracts | `docs/architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md` | ✅ present |
| SVG finish / letter groups direction | `docs/architecture/SVG_FINISH_ASSIGNMENT_AND_LETTER_GROUPS_DIRECTION.md` | ✅ present |
| V2 reference code pack | `tmp/intake-v2-reference-pack/` (52 files + README) | ✅ present (untracked) |
| Atoms multi-layer SVG prompt | `tmp/atoms_multi_layer_svg_prompt.md` | ✅ present (untracked) |

---

## 1. Verdict scurt

**PASS — roadmap validat pe cod real V2/V3.**

Intake V3 backend este deja **superset arhitectural** (production truth, guards, read-only previews). UI-ul actual (`IntakeV3App`) este un **technical/debug stack** (~25 flow steps, 20+ panouri) — **nu** este destinația finală operator.

**Decizie centrală:**

```text
Nu finisăm pagina actuală Intake V3 ca Operator Workspace.
Construim o pagină UI nouă de la zero (presentation layer),
folosind motorul, API-urile, contractele și boundary-urile V3 existente.
Pagina veche rămâne temporar ca technical/debug/legacy view.
```

**Rezultat țintă:**

```text
V2 practical operator workflow
+ V3 production truth
+ V3 guards
+ V3 read-only production previews
+ UI nou, curat, tabbed/pipeline, layer-based
```

---

## 2. Pre-flight

Executed at roadmap authoring time:

```powershell
Set-Location C:\Users\offic\workos
git status --short
git log -10 --oneline
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
```

| Field | Value |
|-------|-------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD** | `b4d8500495f42cf2b8f5cebcc99571a37c9932e6` |
| **Latest commit** | `b4d8500` — `fix(intake-v3): repair SVG file picker upload path` |
| **Git status inițial** | `?? docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md`, `?? tmp/` |
| **Tracked modifications** | **None** — safe to proceed |
| **Only untracked audit/tmp** | Yes |
| **`backend/dev.db`** | Not touched |

Recent Intake V3 commits on branch (context):

```text
b4d8500 fix(intake-v3): repair SVG file picker upload path
1eac137 feat(intake-v3): consolidate production preview UI
7f9c93c feat(intake-v3): add procurement preview from material availability
707030a feat(intake-v3): add read-only material availability check
222ef9d feat(intake-v3): audit and expose layer role confirmation propagation
1b02326 feat(intake-v3): add operator confirmation for SVG layer roles
```

---

## 3. Scope și non-scope

### In scope (across phased builds)

| Area | Scope |
|------|-------|
| **New Operator Workspace page** | New React page + route; tabbed/pipeline UI; V2-superset presentation |
| **Reuse V3 APIs** | `frontend/src/lib/intakeV3/api.ts` clients unchanged in contract |
| **V2 UX recovery** | ColorRegistry, finish cards, lighting/PSU, readiness repair, saved SVG state |
| **Layer-based workflow** | Generic N-layer UI; free layer names; operator-confirmed roles |
| **Legacy view retention** | Current `IntakeV3App` preserved as technical/debug |
| **Tests** | Vitest per phase; backend pytest only when schema extends |

### Explicit non-scope (all phases unless dedicated build approved)

```text
CostEngine changes
Inventory mutations / StockMovement
ExecutionTask / ExecutionPlan creation
PurchaseOrder / SupplierOrder
Quote/order pricing logic changes
DB migrations without approved BUILD doc
Weakening V3 guards or fail-closed semantics
Cosmetic polish-only on IntakeV3App as substitute for new page
Deleting legacy V3 page before parity
ColorRegistry wired as automatic pricing source
```

---

## 4. Principiul V3 Operator Workspace

### Regula centrală

```text
Nu pierdem nicio funcionalitate practică utilă din V2.
Tot ce era util în V2 trebuie regăsit în V3,
într-o formă mai stabilă, logică, curată, sigură și mai cuprinzătoare.
```

### Formula

| Layer | Source |
|-------|--------|
| Operator flow clarity | V2 five-zone model, next action, ColorRegistry |
| Production truth | V3 raw vs confirmed model, layer roles, holes ≠ letters |
| Safety | V3 guard chain, preview-only production panels |
| Depth | V3 material/procurement/task dry-run (read-only) |

### Boundary invariant

```text
Presentation may change; contracts and guards may not weaken.
Missing data → block / 422 — never silent defaults.
```

---

## 5. Ce păstrăm din V3 (backend + capabilities)

Verified in code — **do not remove or bypass**:

| Capability | Frontend evidence | Backend evidence |
|------------|-------------------|------------------|
| Workspace CRUD + field patch | `IntakeV3FieldEditor`, `patchIntakeV3WorkspaceFields` | `intake_v3_workspace_field_editor_service.py` |
| SVG upload + raw analysis | `IntakeV3SvgUploadPanel`, `uploadIntakeV3WorkspaceSvg` | workspace SVG endpoints |
| Raw ≠ confirmed production model | `IntakeV3RawSvgAnalysisPanel`, `IntakeV3ProductionModelReviewPanel` | `RawSvgAnalysis`, `ConfirmedProductionModel` |
| Layer role confirmation | `IntakeV3LayerRoleConfirmationPanel` | `IntakeV3LayerRoleConfirmation*` schemas |
| Layer role propagation | `IntakeV3LayerRolePropagationPanel` | propagation endpoints |
| Finish global/group/letter | `IntakeV3FinishAssignmentPanel` | `FinishAssignment`, `IntakeV3LetterGroupFinishAssignment` |
| Readiness + blockers | `IntakeV3ReadinessPanel`, `IntakeV3PreviewShell` | `ReadinessReport` |
| Guarded quote chain | DryRun → GuardPolicy → Bridge → Enablement → CreateDraftQuote → … | `intake_v3.py` guard models |
| Production previews (read-only) | `IntakeV3ProductionPreviewPanel` | material breakdown, availability, procurement, task dry-run |
| Geometry / perimeter | `IntakeV3GeometryMetricsPanel`, `IntakeV3PathPerimeterClassificationPanel` | snapshot endpoints |
| Fail-closed flags | panel copy | `MaterialIntent.inventory_mutation_allowed = false`, forbidden field paths |

Current UI stack (`IntakeV3App.tsx`): imports **30+ panels**, `deriveFlowSteps` with **25 step IDs** (`flowState.ts`). This is valuable as **technical reference**, not as operator default.

---

## 6. Ce recuperăm din V2

From audit + `tmp/intake-v2-reference-pack/`:

| V2 capability | V2 source | V3 gap | Phase |
|---------------|-----------|--------|-------|
| Five-zone checklist + repair jumps | `zoneLabels.ts`, readiness card | 25-step stepper | 1 |
| Saved SVG filename + timestamp | `V2SvgStage.tsx` | partial after `b4d8500` | 1–2 |
| ColorRegistrySelect (Oracal/RAL/swatch) | `colorRegistry/` | FieldEditor free text | 2 |
| Face vinyl toggle + 651/8500/641 | `V2ProductionStage`, `letterGroupFinishUi.ts` | enum only | 2 |
| Return cant tri-state (stock/RAL/Oracal) | `LetterGroupReturnCantFields.tsx` | partial enums | 2 |
| Group finish card layout | `V2LetterGroupFinishesSection.tsx` | plain FinishAssignment | 2–3 |
| Policromie / printed artwork | `V2ArtworkPolicromieCard`, `svgArtworkFinishAssignments.ts` | **no V3 equivalent** | 3–4 |
| LED / PSU planning | `V2LightingStage`, `lightingPlanning.ts`, `psuAllocation.ts` | boolean `illuminated` only in field editor | 5 |
| Header next action + quote blocker | `WorkIntakeV2OperationalHeader.tsx` | scattered command bar | 1 |
| Quote preview summary | `VolumetricLettersQuotePreview.tsx` | PreviewShell (dense) | 1 |
| Geometry trust / stale badges | `geometrySync.ts` | exists but buried | 2 |

---

## 7. Gap-uri reale între Atoms target și V3 contracts

| Atoms / operator target | V3 today | Gap type |
|-------------------------|----------|----------|
| One row per detected layer: role + finish + color | Layer role per `layer_key`; finish on global/group/letter | **Architectural** — no `layer_finish_assignments[]` |
| Free layer names (`Albastru`, `Logo`, `Layer 12`) | `layer_name` on confirmation layer — ✅ evidence field | UI only in Phase 1–2 |
| Operator-confirmed role drives fields | `confirmed_role` on layer — ✅ | UI role→fields mapping needed |
| Policromie layer (print + laminate + contour) | `printed_vinyl` enum on face finish only; no artwork assignment model | **Backend/schema** Phase 4 |
| ColorRegistry swatch selection | color_code/name text fields in patch allowlist | **Frontend-only** Phase 2 |
| N productive layers, different finishes | letter_group API can approximate 1:1 | **Workaround** Phase 1–2; native Phase 3 |
| LED modules, wattage, PSU reserve +30% | `LedMaterialIntent`, `PowerSupplyIntent` in schema; **not** in field editor allowlist | **Backend patch allowlist** Phase 5 |
| `illumination_mode` frontlit/backlit | Not in V3 workspace patch paths | **Schema/UI** Phase 5 |
| Single next action | readiness has data; UI doesn't derive one CTA | Frontend Phase 1 |
| Tabbed operator zones A–F | Single scroll stack | Frontend Phase 1 |

**Note on Atoms prompt:** `tmp/atoms_multi_layer_svg_prompt.md` uses illustrative names like `LITERE_ROSU` — acceptable for mock data only. **Implementation must not hardcode color/role layer names as production truth.**

---

## 8. Modelul paginii noi: UI de la zero, nu polish

### Ce NU facem

```text
❌ Reorder panels inside IntakeV3App and call it "Operator Workspace"
❌ Hide panels with CSS only without new information architecture
❌ Duplicate business logic in a parallel frontend state machine
```

### Ce facem

```text
✅ New page component tree (e.g. IntakeV3OperatorWorkspaceApp)
✅ New route; workspace id in URL (align with V2 /intake-v2/:id pattern)
✅ Reuse existing API functions from lib/intakeV3/api.ts
✅ Optional: extract shared panel logic into hooks; legacy page imports same hooks
✅ Keep IntakeV3App at legacy route until parity checklist green
```

### Routing proposal (validated on `App.tsx`)

**Current:**

```tsx
<Route path="/intake-v3" element={<IntakeV3App />} />
```

**Recommended transition:**

| Route | Page | Role |
|-------|------|------|
| `/intake-v3` | Workspace list / create / link hub | Entry (can stay on legacy app initially) |
| `/intake-v3/:workspaceId/operator` | **New** `IntakeV3OperatorWorkspaceApp` | **Default operator workspace** (Phase 1+) |
| `/intake-v3/:workspaceId/technical` | Existing `IntakeV3App` (workspace id prop/param) | Debug/legacy full stack |

Rationale: nested `:workspaceId` matches RESTful workspace identity; `/operator` suffix avoids breaking bookmarked `/intake-v3` during rollout. Alternative `/intake-v3/operator/:workspaceId` is acceptable if router prefers action-first — **pick one in Phase 1 BUILD doc**.

---

## 9. Roadmap pe faze

### Faza 0 — Roadmap & contract lock ✅ (this document)

**Scope:** Documentation only.  
**Output:** Boundary map, phase PASS criteria, architectural decisions locked.  
**No code.**

---

### Faza 1 — New Operator Workspace Shell (frontend-only)

**Goal:** Functional tabbed operator page using existing V3 APIs — **no schema changes**.

**Deliverables:**

| # | Item |
|---|------|
| 1 | New route `/intake-v3/:workspaceId/operator` |
| 2 | Header: workspace code, client, template, status, save state, **single next action** from readiness |
| 3 | Pipeline tabs mirroring audit zones A–F (presentation map of `flowState`, not 25 steps) |
| 4 | **C1** SVG: upload (reuse panel logic), saved analysis, production model summary |
| 5 | **C2** Layers: layer role list from API; **no native layer finish** — show role confirmation only |
| 6 | **C3** Dimensions: FieldEditor dimensions |
| 7 | **C4** Global finishes + group/letter via existing `FinishAssignmentPanel` API (advanced collapsed) |
| 8 | **C4** Backing/support: FieldEditor controlled fields |
| 9 | **D** Readiness card + guarded draft quote (CreateDraftQuote when enabled) |
| 10 | **E** Production preview — collapsed; load on expand |
| 11 | **F** Advanced technical — collapsed; link to `/technical` route |
| 12 | Link "Open technical view" → legacy page |

**Explicitly forbidden in Phase 1:**

```text
layer_finish_assignments[] backend
policromie backend
inventory / execution / PO actions
schema / migrations
CostEngine
```

**Temporary workaround (optional):** Map productive layers to synthetic `letter_group` labels via existing `patchIntakeV3FinishAssignments` — **UI-only**, documented as debt until Phase 3. Do not present groups as primary mental model in tab C2.

**PASS:** Operator can complete SVG → confirm model → confirm layer roles → global finish → see readiness → create guarded draft quote when allowed — on **new page only**.

---

### Faza 2 — V2 Practical Controls Recovery (frontend mostly)

**Goal:** Port V2 operator controls into new workspace UI.

| Item | Action |
|------|--------|
| `ColorRegistrySelect` | Import from `frontend/src/components/workos/colorRegistry/` into finish/dimension zones |
| Oracal 651 / 8500 / 641 | Wire to existing `finish_type` + `material_family` + patch paths |
| RAL | Registry + approximate note (existing `ralColors.ts`) |
| Return/cant fields | Port `LetterGroupReturnCantFields` patterns |
| Face vinyl toggle | V2-style toggle → `finish_assignment.face_finish.enabled` |
| Roll width, return depth | FieldEditor + registry context |
| Finish summary mini-card | New presentation component |
| Saved SVG `file_name` + timestamp | From `raw_svg_analysis` |
| Geometry trust / stale | Badges from layer role propagation + geometry endpoints |
| Readiness repair jumps | Scroll/tab navigation to C1–C4 |

**Forbidden:** Native layer finish schema unless Phase 3 BUILD approved separately.

---

### Faza 3 — Native Layer Role + Layer Finish & Multi-Layer SVG

**Goal:** Align UI with Atoms multi-layer model using **production-truth finish per layer**.

**Architectural decision (firm recommendation): Option A — native `layer_finish_assignments[]`**

See §13 for full analysis. Phase 3 **includes backend BUILD** with:

- Schema: `IntakeV3LayerFinishAssignment` (layer_key, role, face/return/backing components, confirmed flag)
- Persistence on workspace payload + quote snapshot propagation
- Readiness rules: unconfirmed productive layer finish → blocker
- Quote preview adapter summary by layer
- Backwards compatibility: global/group/letter remain for advanced overrides

**UI:** Generic layer card list — filter/search/collapse confirmed; scale to 10+ layers.

**Phase 3 forbids:** Hardcoded layer names; per-letter-first workflow.

---

### Faza 4 — Policromie / Printed Artwork

**Goal:** First-class printed artwork layer — not reducible to Oracal face vinyl.

**Requires backend** (unless Phase 3 schema already includes `PrintedArtworkFinishSpec`):

- Role: `printed_artwork` / `logo`
- Fields: print method, laminate, contour cut, white ink/backing optional, notes, area estimate
- Readiness + quote preview line for policromie
- Production preview material need (read-only)

**V2 reference:** `V2ArtworkPolicromieCard`, `svgArtworkFinishAssignments.ts` — **no V3 workspace equivalent today**.

---

### Faza 5 — Lighting / LED / PSU Recovery

**Goal:** V2LightingStage parity within V3 safety.

**Current V3 state (code audit):**

| Field | In schema | In field editor allowlist |
|-------|-----------|---------------------------|
| `support_context.illuminated` | ✅ | ✅ |
| `support_context.shared_support` | ✅ | ✅ (as support_mode) |
| `psu_packed_at_packaging` | ✅ OperationFlags | ❌ |
| `led_materials[]` | ✅ MaterialIntent | ❌ |
| `power_supplies[]` | ✅ MaterialIntent | ❌ |
| `illumination_mode` (frontlit/backlit) | ❌ | ❌ |
| `led_system`, `module_power`, `required_watts+30%` | V2 libs only | ❌ |

**Recommendation:** Phase 5 is **split**:

1. **5a (frontend):** UI port from `V2LightingStage` + `lightingPlanning.ts` — persist via **new approved patch paths** or workspace sub-object PATCH (requires small backend BUILD).
2. **5b:** Quote preview + readiness warnings for missing PSU plan.

**Rule:** No shared support → PSU packed in delivery (`psu_packed_at_packaging` / V2 `psuAllocation`).

---

### Faza 6 — E2E Hardening & Stress Fixtures

**Goal:** Regression safety across V2 parity + V3 guards.

**Scenarios:**

| Scenario | Validates |
|----------|-----------|
| Simple: 1 letter layer + cant + backing | Happy path |
| Multi-color: 2+ productive layers, different finishes | Layer finish native |
| Logo policromie | Phase 4 |
| 10-layer stress | UI scale, performance |
| SVG missing units / manual fallback | Fail-closed UX |
| Stale geometry / layer snapshot | Propagation warnings |
| Readiness warnings | Blockers visible |
| Guarded quote creation | `can_create_quote` |
| Production preview | Read-only, stage-gated |
| **Negative:** no inventory mutation, no ExecutionTask, no PO | Boundary tests |

---

## 10. Contracte/API reutilizabile

All clients in `frontend/src/lib/intakeV3/api.ts` — **reuse without fork**:

| Domain | Key functions |
|--------|---------------|
| Workspace | `getIntakeV3Workspace`, `updateIntakeV3Workspace`, `fetchIntakeV3WorkspacePreview` |
| Fields | `patchIntakeV3WorkspaceFields`, `fetchIntakeV3EditableFields` |
| SVG | `uploadIntakeV3WorkspaceSvg` |
| Production model | `fetchIntakeV3ProductionModelReviewCandidate`, `confirmIntakeV3ProductionModel` |
| Layer roles | `fetchIntakeV3WorkspaceLayerRoleConfirmation`, `saveIntakeV3WorkspaceLayerRoleConfirmation`, propagation + refresh |
| Finishes | `fetchIntakeV3FinishAssignments`, `patchIntakeV3FinishAssignments`, targets |
| Readiness / quote | dry-run, guard policy, bridge, enablement, create draft, review, pricing, accept/convert |
| Production preview | material breakdown, availability, procurement, task dry-run, geometry, perimeter |

Backend router: `backend/routers/intake_v3_workspaces.py` — prefix `/api/v1/intake-v3/`.

Frontend types: `frontend/src/lib/intakeV3/contracts.ts` + domain contract files.

**Do not duplicate HTTP paths in new page — import from `api.ts`.**

---

## 11. Gap-uri care cer backend/schema

| Gap | Phase | Proposed contract |
|-----|-------|-------------------|
| `layer_finish_assignments[]` | 3 | New list on workspace + snapshot propagation |
| Printed artwork / policromie assignment | 4 | `IntakeV3PrintedArtworkFinishAssignment` or extend layer finish |
| LED/PSU controlled fields | 5 | Extend `ALLOWED_CANONICAL_PATHS` + nested lighting plan object |
| `illumination_mode` enum | 5 | `SupportContext` or `LightingPlan` sub-object |
| Layer finish readiness blockers | 3 | `intake_v3_readiness_service.py` rules |
| Quote preview multi-layer summary | 3–4 | Adapter in pricing input builder |

**Not required for Phase 1–2:** any of the above.

---

## 12. Strategia multi-layer SVG

### Unitatea principală

```text
layer detectat → operator-confirmed role → conținut → material/finisaj → status
```

### Reguli

| Rule | Detail |
|------|--------|
| **Layer name is input evidence, not production truth** | `layer_name` from SVG/parser; display only |
| **Operator-confirmed role is production truth** | `confirmed_role` on `IntakeV3LayerRoleConfirmationLayer` |
| Free names | `Albastru`, `Rosu`, `Logo`, `Cant`, `Spate`, `Gauri`, `Ghidaj`, `Layer 12`, `Text exterior`, `Folie 1`, … |
| Suggestions | System may suggest role from name/color/geometry (`auto_role`, `auto_confidence`) — operator confirms |
| Main operator count | **Confirmed letters** from production model — not holes, not guides |
| Holes / guides | Technical/reference roles — no finish required |
| Per-letter override | Advanced only, collapsed (C5) |
| Scale | Same card component for 2 or 10+ layers — search/filter/collapse completed |

### Per-layer operator flow (target UI)

1. Display detected name + evidence (fill/stroke, path count, closed paths, bbox, confidence)
2. Operator selects production role (Face/Letters, Return/Cant, Backing, Printed Artwork, Technical cutouts, Ignore/Reference)
3. UI shows role-specific fields
4. Operator selects material/finish/color (Phase 2+ registry)
5. Operator confirms layer

**Anti-pattern (forbidden):**

```text
❌ Hardcoded UI sections LITERE_ROSU / LITERE_ALBASTRU
❌ Treating layer name "Albastru" as automatic Oracal 527 assignment
```

---

## 13. Strategia layer role / layer finish

### Situație actuală (verified)

```text
V3 has layer role per layer_key (IntakeV3LayerRoleConfirmationLayer).
V3 has finish via FinishAssignment: global + letter_group + letter.
V3 does NOT have layer_finish_assignment nativ.
```

Decoupling gap: operator confirms role on layer A, but assigns finish on letter_group B — mental mismatch.

### Opțiunea A — `layer_finish_assignments[]` nativ ✅ **RECOMMENDED Phase 3**

**Pros:**

- Clean alignment with Atoms layer-row model
- Scales to 10+ layers with free names
- Correct for designer-prepared multi-layer SVG
- Reduces group/letter workaround as primary path
- Enables policromie as layer-scoped assignment

**Cons / work:**

- Schema + API + migration/fallback strategy
- Readiness + quote snapshot adapter updates
- Backwards compatibility for existing workspaces

### Opțiunea B — mapping temporar `layer_key → letter_group`

**Pros:**

- Faster Phase 1–2 unblock using `patchIntakeV3FinishAssignments`
- No backend in early phases

**Cons:**

- Workaround debt; layer ≠ group conceptually
- Policromie/logo awkward
- Poor scale for many layers
- Risk teams treat mapping as permanent

### Recommendation

| Phase | Strategy |
|-------|----------|
| **1–2** | Option B **allowed only as hidden/Advanced debt** — do not market as primary UX |
| **3+** | **Option A mandatory** — dedicated BUILD with pytest + QA doc |

---

## 14. Strategia policromie / printed artwork

**V2 has:** `V2ArtworkPolicromieCard`, `svgArtworkFinishAssignments.ts` — artwork finish assignments separate from letter groups.

**V3 has:** `printed_vinyl` as face finish enum value — **not** a full policromie layer model.

**Target layer example:**

```text
Detected: Logo
Role: Printed Artwork / Logo
Treatment: Printed vinyl + laminate
Contour cut: yes/no
White ink / white backing: optional manual
Print notes
Area estimate (if geometry available)
Status: Confirmed
```

**Phase placement:** Phase 4 (or Phase 3 if schema designed holistically with layer finish).

**Backend gap:** Marked **required** — cannot be frontend-only if quote/production preview must reflect policromie distinctly.

---

## 15. Strategia ColorRegistry / Oracal / RAL

### Port plan

| Control | Implementation |
|---------|----------------|
| `ColorRegistrySelect` | Reuse `frontend/src/components/workos/colorRegistry/` |
| Oracal 651 / 8500 / 641 | Map selection → `material_family`, `material_code`, `color_code`, `color_name` patch paths |
| RAL | `ralColors.ts` + swatch + **approximate match note** |
| Swatch | Registry hex preview — display only |
| Roll width | Existing `face_vinyl_roll_width_mm` path |

### Pricing boundary

```text
ColorRegistry is for operational visual selection — NOT a pricing source.
Do not wire registry into CostEngine rates (per AGENTS.md).
```

### Phase

- **Phase 2:** frontend-only wiring to existing patch allowlist fields
- **Phase 3+:** layer-scoped color fields on native layer finish assignment

---

## 16. Strategia lighting / LED / PSU

### V2 reference

- `V2LightingStage.tsx`
- `lightingPlanning.ts`, `psuAllocation.ts`
- `syncLightingPlanning` pattern

### V3 gaps

Field editor allowlist (`intake_v3_workspace_field_editor_service.py`) includes only `support_context.illuminated` — not LED arrays, PSU wattage, override reason.

Schema already defines `LedMaterialIntent`, `PowerSupplyIntent`, `psu_packed_at_packaging` — **intent model exists; operator input path incomplete**.

### Phase 5 deliverables

- Illumination mode: frontlit / backlit / non-illuminated
- LED modules vs strip, light color, module power
- Consumption, required +30%, PSU capacity, reserve
- Auto proposal + manual override + override reason
- No shared support → PSU in delivery bundle

**Decision:** Phase 5 requires **backend BUILD** to extend patch allowlist or add `lighting_plan` sub-resource — not pure frontend.

---

## 17. Strategia readiness / quote preview

### Operator view (Zone D)

```text
Blockers (hard stop)
Warnings (can proceed with caution)
Next recommended action (single CTA)
Repair links → tab/section jump
Guarded draft quote button (respects can_create_quote)
```

### Advanced view (Zone F / technical route)

```text
Guard policy, bridge, snapshot policy
Enablement internals
Accept/convert guarded panels
Full dry-run payloads
```

### Quote preview summary (not debug dump)

Summarize: dimensions, confirmed letter count, productive layers + roles, finishes, policromie, backing, lighting/PSU, warnings.

Reuse `IntakeV3PreviewShell` data — new compact `OperatorQuoteReadinessCard` component.

**Rule:** Hiding guard details in default view **must not** hide blockers.

---

## 18. Strategia production preview

Keep all V3 read-only previews — **rehome presentation** in Zone E.

| Preview | Before quote | After draft quote | After order |
|---------|--------------|-------------------|-------------|
| Geometry metrics | Expand if stale warning | ✅ | ✅ |
| Material breakdown | Collapsed / preview_only | ✅ | ✅ |
| Material availability | Locked or collapsed | Partial | ✅ |
| Procurement preview | Locked | Partial | ✅ |
| Task dry-run | Locked | Preview | ✅ |
| Order production readiness | N/A | N/A | ✅ |

**UI rules:**

- Grouped cards, collapsed by default
- No 10 simultaneous "unavailable" panels
- No buttons implying inventory reservation, task creation, PO

Existing consolidation: `IntakeV3ProductionPreviewPanel` (`1eac137`) — reuse subsection logic in new page.

---

## 19. Strategia technical/debug legacy view

### Recommended (safest)

| Item | Decision |
|------|----------|
| Legacy page | Keep `IntakeV3App` at `/intake-v3/:workspaceId/technical` |
| Default operator | New page at `/intake-v3/:workspaceId/operator` |
| 25-step stepper | Remains in technical view Zone F equivalent |
| Parity gate | Do not remove technical route until Phase 6 checklist PASS |
| Hub | `/intake-v3` lists workspaces with links to both views during transition |

### Later (post Phase 6)

- Redirect operator default from hub to `/operator`
- Technical view behind "Advanced" link only

---

## 20. Test strategy

### Frontend tests (Vitest) — per phase

| Test | Phase |
|------|-------|
| New route renders operator workspace | 1 |
| Tabs switch content; checklist maps to sections | 1 |
| Legacy technical route still accessible | 1 |
| Header next action from readiness | 1 |
| SVG saved filename displayed | 2 |
| Production model count = letters not holes | 1 |
| Layers grouped production / technical / ignored | 1 |
| Layer names treated as evidence in copy/labels | 1 |
| Operator selects role per layer | 1 |
| Role-dependent fields visibility | 3 |
| Advanced overrides collapsed by default | 1 |
| Technical details collapsed | 1 |
| Guarded quote respects `can_create_quote` | 1 |
| No forbidden action buttons in DOM | 1 |
| ColorRegistry selection patches allowed fields | 2 |
| Multi-layer finish cards | 3 |
| Policromie layer fields | 4 |
| Lighting/PSU form persistence | 5 |

### Backend tests (pytest) — phases with schema

| Test | Phase |
|------|-------|
| `layer_finish_assignments` persistence | 3 |
| Layer finish readiness blockers | 3 |
| Printed artwork assignment | 4 |
| Quote preview multi-layer summary | 3–4 |
| Backwards compatibility old payloads | 3 |
| Free layer names + operator roles | 3 |
| Lighting patch allowlist | 5 |

### E2E / scenario (Phase 6)

Playwright or scripted smoke — extend `work-intake` patterns where applicable; multi-layer fixtures in `tmp/` as reference for seed scripts (dedicated BUILD).

---

## 21. Risk matrix

| Risk | Phase | Impact | Mitigation | Owner decision? |
|------|-------|--------|------------|-----------------|
| Mock Atoms ahead of backend | 1–3 | UI promises unavailable APIs | Phase 1 uses real APIs only; mock data in Storybook only | No |
| layer_finish vs group mapping ambiguity | 1–2 | Wrong production truth | Document debt; cap Phase 2; force Phase 3 native | **Yes** — approve Phase 3 BUILD |
| Assuming layer names are production truth | all | Mis-costing | Enforce copy + tests; role confirmation required | No |
| ColorRegistry mistaken as pricing | 2 | CostEngine coupling | AGENTS.md boundary; code review | No |
| Hiding guard details too much | 1 | Unsafe quote | Blockers always in Zone D | No |
| Old/new page duplication | 1–6 | Maintenance | Shared hooks from `lib/intakeV3/`; delete legacy only after parity | No |
| Schema migration risk | 3–5 | Broken workspaces | Versioned payload + fallback readers | **Yes** |
| Policromie under-modeled | 4 | Missing quote lines | Dedicated schema in Phase 4 BUILD | **Yes** |
| LED/PSU scope creep | 5 | Delay | Split 5a UI / 5b backend; reuse V2 libs | No |
| Multi-layer quote preview complexity | 3–4 | Wrong summaries | Adapter tests + fixture jobs | No |
| Accidental unsafe actions | all | Production incident | No new buttons; reuse read-only panels | No |
| Polishing IntakeV3App instead of new page | 1 | Permanent debt | This roadmap forbids; review rejects | No |

---

## 22. Build order recomandat

**Firm order** (do not parallelize Phase 3 backend with Phase 4 without coordination):

```text
1. Faza 0 — Roadmap & contract lock (this document)
2. Faza 1 — New Operator Workspace Shell (frontend-only)
3. Faza 2 — ColorRegistry + V2 finish UX recovery (frontend mostly)
4. Faza 3 — Native layer_finish_assignments backend + UI
5. Faza 4 — Printed artwork / policromie layer
6. Faza 5 — Lighting / LED / PSU (backend patch + UI)
7. Faza 6 — E2E hardening + multi-layer stress fixtures
```

**Justification:** Shell first proves routing and guard presentation without schema risk; registry recovery gives operator value before heavy backend; native layer finish unlocks multi-layer truth; policromie and lighting depend on stable layer model; E2E last validates full stack.

---

## 23. PASS/FAIL criteria per fază

| Phase | PASS | FAIL |
|-------|------|------|
| **0** | Roadmap merged; decisions recorded | Generic doc; no code refs |
| **1** | New route works; tabs; readiness CTA; guarded quote; legacy link; no schema change; targeted Vitest green | Polish-only on IntakeV3App; missing next action |
| **2** | ColorRegistry on finishes; return/cant; saved filename; repair jumps | Registry wired to pricing |
| **3** | Native layer finish persisted; readiness blocks unconfirmed; 2-layer + 10-layer tests | Permanent group mapping as primary |
| **4** | Policromie layer quote/preview line | Logo forced through Oracal-only |
| **5** | LED/PSU persisted via approved paths | Execution/inventory side effects |
| **6** | All scenarios PASS; negative boundary tests; operator default route ready | Legacy removed prematurely |

---

## 24. Prompt skeleton pentru Faza 1

Use as Cursor build prompt (adapt paths/HEAD at run time):

```markdown
# BUILD: Intake V3 Operator Workspace — Phase 1 Shell (frontend-only)

## Boundary
- Create NEW UI page — do NOT polish IntakeV3App as the operator default.
- Frontend only: no backend, schema, migrations, dev.db, CostEngine, inventory, ExecutionTask, PO.
- Reuse existing V3 API clients in frontend/src/lib/intakeV3/api.ts — no duplicated HTTP logic.
- Keep V3 guards fail-closed; no unsafe action buttons.

## Read first
- docs/architecture/INTAKE_V3_OPERATOR_WORKSPACE_IMPLEMENTATION_ROADMAP.md
- docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md

## Deliver
1. Route: /intake-v3/:workspaceId/operator → new IntakeV3OperatorWorkspaceApp (name flexible).
2. Legacy: link to /intake-v3/:workspaceId/technical (existing IntakeV3App wired to workspace id).
3. Header: workspace, client, template, status, save state, single next action from readiness.
4. Tabs/sections A–F: Input (SVG, layers roles only, dimensions, global finish, backing/support),
   Quote readiness + guarded draft quote, Production preview collapsed, Technical collapsed.
5. Reuse/adapt: SvgUploadPanel, ProductionModelReview, LayerRoleConfirmation, FieldEditor,
   FinishAssignment (advanced collapsed), ReadinessPanel, CreateDraftQuote, ProductionPreviewPanel.
6. Layer UX: show detected layer_name as evidence; operator confirms role — never treat name as production truth.
7. Tests: route render, tab switch, next action, can_create_quote gate, legacy link, no forbidden buttons.

## QA
- docs/qa/BUILD_INTAKE_V3_OPERATOR_WORKSPACE_PHASE1.md
- npm run test:frontend -- <new test files>
- Confirm git diff excludes backend/

## PASS
Operator can walk SVG → model → layer roles → global finish → readiness → guarded quote on NEW page only.
```

---

## 25. Autoevaluare

| Criterion | Score | Notes |
|-----------|-------|-------|
| Based on real V2/V3 code | **10/10** | Inspected `IntakeV3App.tsx`, `flowState.ts`, `api.ts`, `intake_v3.py`, field editor allowlist, `App.tsx` routing |
| New page vs polish explicit | **10/10** | §8, §9 Faza 1, §24 |
| V3 safety preserved | **10/10** | Non-scope + production preview rules |
| V2 recovery mapped | **9/10** | From audit + reference pack |
| Phased with boundaries | **10/10** | Phases 0–6 with PASS/FAIL |
| Frontend vs backend separated | **10/10** | §9–11 |
| Multi-layer generic (not hardcoded colors) | **10/10** | §12–13 |
| layer_finish decision firm | **10/10** | Option A Phase 3 |
| Policromie, ColorRegistry, LED/PSU | **9/10** | Gaps marked with schema needs |
| Test strategy + risks + Phase 1 prompt | **10/10** | §20–24 |
| No application code modified | **10/10** | This file only |

**Roadmap verdict: PASS**

---

*End of roadmap. No application source modified except this document.*
