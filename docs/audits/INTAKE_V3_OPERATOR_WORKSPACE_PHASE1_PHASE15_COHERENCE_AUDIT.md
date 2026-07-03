# Intake V3 Operator Workspace — Phase 1 + Phase 1.5 Coherence Audit

**Date:** 2026-06-19  
**Type:** Read-only audit — no application changes  
**Auditor scope:** Architectural coherence, not visual pixel parity  
**HEAD audited:** `15473673d6cf09522ea6ff3d59dc9b39785aa225`  
**Branch:** `local/integration-pr4-plus-svg-path`

---

## 1. Verdict scurt

**PASS WITH CLEANUP**

Implementarea actuală **este o bază coerentă** pentru fazele următoare, **nu** un eșec care cere refacere de la zero. Phase 1 a creat structură reală (pagină nouă, routing, hook, tab shell, layer setup operator-facing). Phase 1.5 a adăugat un **presentation layer util**, nu doar CSS ad-hoc.

Totuși, rezultatul rămâne **în mare parte un shell operator peste panouri tehnice V3 existente**, stilizat spre Atoms. Fără un **BUILD_CLEANUP** scurt înainte de Faza 2, riscul de datorie (duplicare fetch/state, inconsistență vizuală în panouri legacy, încărcare eager) va crește.

**Recomandare:** **D** — păstrează `66ebd81` + `1547367`, fă cleanup țintit, apoi Faza 2.

---

## 2. Executive summary

| Question | Answer |
|----------|--------|
| Bază coerentă sau shell + styling? | **Ambele, în ordinea asta:** shell coerent Phase 1 → styling + presentation tokens Phase 1.5 |
| Poate fi păstrată? | **Da**, la `1547367 |
| Trebuie refăcută cap-coadă? | **Nu** — rebuild de la `b4d8500` ar arunca structură validă |
| Sigur pentru Faza 2? | **Da, după cleanup mic** (dedup fetch, lazy tabs, docs lock) |

Phase 1 (+2249 LOC) a livrat exact ce promite roadmap-ul Faza 1: rută nouă, header, 10 taburi, reutilizare API V3, layer role cards, legacy technical view. Nu a „finisat” `IntakeV3App`.

Phase 1.5 (+874 / −389 LOC) a extras `operatorWorkspacePresentation.tsx`, a uniformizat cardurile și header-ul Atoms, a adăugat checklist chips — **refactor presentation rezonabil**, fără boundary break.

Gap-ul principal față de Atoms final-reviewed și față de V2 operator UX: **conținutul taburilor încă arată ca panouri debug V3 învelite în carduri**, nu ca workflow operator complet (ColorRegistry, finish per layer, SVG preview, LED/PSU planning interactiv).

---

## 3. Pre-flight

### Git commands (executed)

```text
git status --short
git log -5 --oneline
git show --stat 66ebd81
git show --stat 1547367
git diff --stat b4d8500..66ebd81
git diff --stat 66ebd81..1547367
```

### Results

| Item | Value |
|------|-------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD** | `1547367` — `style(intake-v3): align operator workspace with atoms mock` |
| **Phase 1** | `66ebd81` — 22 files, +2249 lines |
| **Phase 1.5** | `1547367` — 18 files, +874 / −389 lines |
| **Untracked** | `docs/architecture/INTAKE_V3_OPERATOR_WORKSPACE_IMPLEMENTATION_ROADMAP.md`, `docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md`, `tmp/` |
| **Tracked dirty** | None (post-commit) |

---

## 4. Ce a făcut Phase 1 (`66ebd81`)

### 4.1 Pagină nouă coerentă?

**Da.** `IntakeV3OperatorWorkspaceApp.tsx` este pagină separată (~67 linii): header + tabs + switch tab conținut. **Nu** este reskin al `IntakeV3App`.

### 4.2 Recompunere panouri vs logică nouă

**Predominant recompunere**, conform intenției roadmap:

| Tab | Tip implementare |
|-----|------------------|
| SVG & Layers | Panouri existente (`SvgUploadPanel`, `ProductionModelReviewPanel`) + **`IntakeV3OperatorLayerSetup` nou** |
| Geometry | `GeometryMetricsPanel`, `PathPerimeterClassificationPanel` |
| Finishes | `FinishAssignmentPanel`, `FinishVariationSummaryPanel` |
| Production Setup | `IntakeV3FieldEditor` |
| Lighting | Read-only din preview/support_context |
| Readiness | `IntakeV3ReadinessPanel` + repair navigation |
| Quote | `PreQuoteReviewPanel`, `CreateDraftQuotePanel` |
| Materials | Material breakdown / availability / procurement panels |
| Production Preview | `IntakeV3ProductionPreviewPanel` + sub-panels |
| Advanced | Guard panels, flow stepper, raw SVG |

Aceasta **este corectă pentru Faza 1** (roadmap: reuse V3 APIs). Nu e rescriere cap-coadă — e **composition shell**.

### 4.3 Component tree

```text
IntakeV3OperatorWorkspaceApp
├── useIntakeV3OperatorWorkspace(workspaceId)
├── IntakeV3OperatorWorkspaceHeader(state)
├── IntakeV3OperatorWorkspaceTabs(activeTab, state)
└── main → IntakeV3Operator*Tab(state) × 10
         └── mostly → existing intake-v3/*Panel components
         └── exception: IntakeV3OperatorLayerSetup (operator-native)
```

**Sănătos ca structură de shell.** Tab-urile sunt thin wrappers — clar separation of concerns pentru presentation routing.

**Slăbiciuni tree:**

- `IntakeV3OperatorLayerSetup` face **fetch duplicat** al layer role confirmation (hook-ul `refreshProductionPanels` îl încarcă deja; componenta refetch-uiește în `useEffect` propriu).
- Footer debug în app: listează toate tab ID-urile — remnant de shell dev, nu operator UX.
- `max-w-6xl` footer vs `max-w-[1100px]` main (Phase 1.5) — inconsistență minoră layout.

### 4.4 Hook / helpers

**`useIntakeV3OperatorWorkspace.ts` (~370 linii):** hook dedicat, clar delimitat. Încarcă workspace, preview, quote guards, production panels. Pattern `refreshAll` / `handleWorkspaceUpdated` este rezonabil.

**Problema:** logică **paralelă cu `IntakeV3App.tsx`** (aceleași fetch-uri quote/production). Nu e copy-paste literal, dar e **fork de state management** — datorie de mentenanță când se adaugă endpoint-uri noi.

**`operatorWorkspaceHelpers.ts`:** funcții pure pentru header, layer status, evidence — **bine plasate**, extensibile pentru Faza 3.

**`operatorWorkspaceTabs.ts`:** constante tab — corect, stabil.

### 4.5 Routing

```text
/intake-v3/:workspaceId/operator  → IntakeV3OperatorWorkspaceApp
/intake-v3/:workspaceId/technical → IntakeV3TechnicalRoute → IntakeV3App(fixedWorkspaceId, variant="technical")
/intake-v3                        → legacy hub (unchanged)
```

**Corect.** Technical legacy păstrat sănătos cu link bidirectional.

### 4.6 Technical legacy view

`IntakeV3TechnicalRoute.tsx` — wrapper minim (27 linii), fără logică duplicată. **`IntakeV3App` primește `fixedWorkspaceId`** — modificare chirurgicală, boundary-respecting.

---

## 5. Ce a făcut Phase 1.5 (`1547367`)

### 5.1 Doar styling?

**Nu exclusiv.** Breakdown:

| Change | Nature |
|--------|--------|
| `operatorWorkspacePresentation.tsx` (new) | **Presentation layer extraction** — tokens, `OperatorCard`, badges, chips |
| Header / tabs refactor | Styling + **checklist chip derivation** (logică ușoară) |
| Tab wrappers | Mostly **layout re-wrap** around same panels |
| `deriveOperatorChecklistChips`, `countPendingLayerSetups` | **Helper logic** (nu doar CSS) |
| Production Setup summary cards | **Read-only derived UI** — cosmetic structure, nu funcție nouă |
| Tests +1 | Checklist chip assertion |

**Concluzie:** ~70% presentation refactor, ~30% operator UX metadata (chips, badges, copy). **Nu** e rescriere funcțională.

### 5.2 Duplicare introdusă?

**Minimă.** Nu s-au duplicat panouri. Risc duplicare **pre-existent** (hook vs IntakeV3App) **nerezolvat**, nu agravat major.

### 5.3 Boundary-uri

**Păstrate.** Phase 1.5 nu atinge backend, nu adaugă acțiuni interzise, nu implementează layer_finish / ColorRegistry / LED persistence. Copy Phase 3–5 rămâne declarativ.

---

## 6. Analiză component tree (stare `1547367`)

### Layers

| Layer | Assessment |
|-------|------------|
| **Page shell** | Coherent, thin |
| **State hook** | Functional, forked from legacy app |
| **Operator-native** | LayerSetup, Header helpers, presentation tokens |
| **Legacy panels** | Still dominant inside tabs — **visual/UX mismatch** |

### Ce funcționează bine

- Separare operator vs technical route
- Tab IDs stabili pentru teste și Phase 2 navigation
- LayerSetup cu grouping productive / technical / ignored
- Advanced collapsed by default
- Test suite acoperă safety boundaries

### Ce creează confuzie pe termen lung

- Același panel arată **diferit** în operator (card wrapper) vs technical (raw) — operator încă „simte” debug UI în interior
- `IntakeV3FinishAssignmentPanel`, `IntakeV3FieldEditor`, `IntakeV3ProductionPreviewPanel` — componente proiectate pentru stack 25-step, nu pentru pipeline operator
- Layer role fetch dublu

---

## 7. Analiză UI/UX față de Atoms final-reviewed

**Reference:** `tmp/atoms-export/intake-v3-operator-workspace-final-reviewed.html`

### Aliniat

| Element | Status |
|---------|--------|
| Dark tokens (`#0A0F1A`, `#111827`, `#2A3548`) | ✓ via `ow` |
| Sticky header: code, client, template, letters metric | ✓ |
| Checklist chips (SVG, model, layers, finishes, lighting, quote) | ✓ (Phase 1.5) |
| Underline workflow tabs | ✓ |
| Layer card: detected name, suggested/confirmed role, evidence, badges | ✓ (parțial) |
| Phase notices (3/4/5) | ✓ copy-only |
| Materials read-only disclaimer | ✓ |
| Advanced discret / collapsed | ✓ |
| Technical view link | ✓ |

### Ne-aliniat / lipsă

| Element | Gap |
|---------|-----|
| **SVG preview thumbnail** | Atoms are `.svg-preview`; React nu |
| **ColorRegistry swatches** (`cpk-*`) per layer/finish | Lipsă — corect Phase 2, dar Atoms le tratează ca UX central |
| **Layer finish UI per layer** | Atoms layer-based finish cards; React doar role select |
| **Finishes tab** | Atoms = finish cards cu swatch search; React = `FinishAssignmentPanel` legacy |
| **Lighting & PSU** | Atoms = LED system, module count, PSU stats, override; React = 4 câmpuri read-only |
| **Readiness** | Atoms = zone checklist A–F; React = `ReadinessPanel` + listă blockers |
| **Materials table** | Atoms = tabel cu swatch + qty; React = panouri tehnice |
| **Single primary CTA** | Atoms sugerează acțiune unică; React = text „Next:” fără buton CTA |
| **Footer tab debug list** | Nu există în Atoms; există în React |

### Ce este doar cosmetizat

- Card wrappers (`OperatorCard`) în jurul panourilor nemodificate
- Stat grids cu date deja disponibile în preview
- Production Setup „Backing / Dimensions / Return fallback” cards — **read-only summaries** peste același `FieldEditor`
- Tab badges (pending layers, blockers) — util, dar superficial față de workflow Atoms

### Concluzie Atoms

Pagina React este **Atoms-inspired shell**, nu **Atoms-complete operator workspace**. Pentru Faza 1/1.5 scope, asta e **acceptabil**. Riscul e perceptual: stakeholder poate crede că parity e ~80% când funcțional e ~35% față de mock.

---

## 8. Analiză față de roadmap

**Reference:** `docs/architecture/INTAKE_V3_OPERATOR_WORKSPACE_IMPLEMENTATION_ROADMAP.md` (untracked — should be committed)

### Faza 1 — respectată?

| Deliverable | Status |
|-------------|--------|
| Route `/operator` | ✓ |
| Header + next action | ✓ (text, nu CTA button) |
| Pipeline tabs A–F map | ✓ (10 tabs superset) |
| SVG upload + saved state | ✓ (filename; timestamp parțial) |
| Layer roles, no native finish | ✓ |
| FieldEditor dimensions/backing | ✓ |
| Global finish + collapsed advanced | ✓ |
| Readiness + guarded quote | ✓ |
| Production preview collapsed | ⚠️ Tab dedicat, panels **eager-loaded** on mount (roadmap said load on expand) |
| Advanced + technical link | ✓ |

**PASS Faza 1** cu observație lazy-load.

### Faza 2/3/4/5 amestecate?

**Nu implementate.** Doar copy „planned Phase N” — **corect**, nu promisiune backend falsă.

### UI promite funcții inexistente?

**Nu în mod activ** (butoane blocate/absente). Copy policromie/LED/layer finish spune explicit „Phase N” — **onest**.

### Boundary checks

| Rule | Status |
|------|--------|
| Materials read-only | ✓ banner + no reservation buttons |
| Quote guarded | ✓ `can_create_quote=false` → disabled button (testat) |
| Layer name = evidence | ✓ header + layer setup copy |
| Layer cards operator-facing | ✓ custom cards, not raw table |
| No unsafe actions | ✓ tested |

---

## 9. Boundary check (consolidat)

```text
✓ no backend changes in Phase 1 or 1.5
✓ no schema / migrations
✓ no CostEngine / inventory mutation / ExecutionTask / PO
✓ legacy technical preserved
✓ real V3 APIs used (not mock-only UI)
✓ guards respected on quote creation
```

**Singura tensiune:** `IntakeV3ProductionPreviewPanel` și sub-panels pot conține butoane/terminologie tehnică — testele verifică absența acțiunilor **interzise explicit**, nu toate acțiunile tehnice posibile din panouri legacy. Worth monitoring in Phase 2.

---

## 10. Technical debt / maintainability risks

### Debt existent (prioritar)

| ID | Risk | Severity | Phase impact |
|----|------|----------|--------------|
| D1 | `useIntakeV3OperatorWorkspace` forks `IntakeV3App` fetch state | Medium | Every new API |
| D2 | LayerSetup duplicate fetch | Low | Performance, race edge cases |
| D3 | Legacy panels inside operator cards — inconsistent UX | Medium | Phase 2–3 feel |
| D4 | Eager `refreshProductionPanels` on load | Low | Perf on large workspaces |
| D5 | Footer debug tab list | Low | Operator polish |
| D6 | Roadmap + V2 audit untracked | Medium | Process / agent confusion |
| D7 | Tailwind token strings vs CSS variables (Atoms uses `:root`) | Low | Theming drift |

### Pregătire faze viitoare

| Phase | Ready? | Notes |
|-------|--------|-------|
| **2 ColorRegistry** | **Moderate** | Finishes tab wraps `FinishAssignmentPanel` — trebuie înlocuit/îmbogățit, nu rescris de la zero |
| **3 layer_finish** | **Good** | `LayerSetup` + helpers extensibile; slot pentru finish section per layer |
| **4 policromie** | **Good** | `isPrintedArtworkCandidate`, violet notes — placeholder onest |
| **5 LED/PSU** | **Good** | Lighting tab separat, read-only — structură pregătită |

**Nu** e prea lipit de mock/temporar. E lipit de **panouri legacy V3** — alt tip de datorie, gestionabil.

---

## 11. Recomandare finală

### **D — Păstrăm commiturile, BUILD_CLEANUP înainte de Faza 2**

**Nu B** (revert 1.5): pierzi `operatorWorkspacePresentation` și header/tabs fără a rezolva problema structurală.

**Nu C** (rebuild de la b4d8500): Phase 1 shell este valid; rebuild = cost mare, același fork hook inevitabil.

**Nu A simplu** (merge direct Phase 2): merge posibil, dar cleanup mic reduce confuzia.

---

## 12. BUILD_CLEANUP plan (dacă D)

### Păstrează (nu rescrie)

- `IntakeV3OperatorWorkspaceApp.tsx` (minus footer debug)
- `IntakeV3TechnicalRoute.tsx`
- `useIntakeV3OperatorWorkspace.ts` (refactor incremental, nu delete)
- `operatorWorkspaceTabs.ts`
- `operatorWorkspaceHelpers.ts`
- `operatorWorkspacePresentation.tsx`
- `IntakeV3OperatorLayerSetup.tsx` (extinde în Phase 3)
- `IntakeV3OperatorWorkspaceApp.test.tsx` (+ extinde lazy-load tests)
- Routes în `App.tsx`
- QA docs Phase 1 + 1.5

### Curăță (BUILD_CLEANUP scope)

| # | Action | Files |
|---|--------|-------|
| 1 | **Remove duplicate layer fetch** — LayerSetup consumă `state.layerRoleConfirmation` only; fetch doar în hook | `IntakeV3OperatorLayerSetup.tsx` |
| 2 | **Lazy-load tab data** — `refreshProductionPanels` / quote panels la primul visit tab (materials, production_preview, advanced) | `useIntakeV3OperatorWorkspace.ts`, tab components |
| 3 | **Remove footer debug** tab ID list | `IntakeV3OperatorWorkspaceApp.tsx` |
| 4 | **Commit docs lock** — roadmap + V2 audit tracked | `docs/architecture/…`, `docs/audits/INTAKE_V2…` |
| 5 | **Document panel boundary** — which legacy panels are wrapped vs must be replaced in Phase 2 | new short note in roadmap or BUILD_CLEANUP QA |
| 6 | **Unify max-width** footer/main | `IntakeV3OperatorWorkspaceApp.tsx` |

### Rescrie (Phase 2+, not cleanup)

- Finishes tab presentation (ColorRegistry) — **Phase 2 build**
- Layer finish section on layer cards — **Phase 3**
- Lighting interactive planning — **Phase 5**

### Șterge

- Footer debug string only (Phase 1 remnant)

### Teste

| Keep | Add in cleanup |
|------|----------------|
| All 11 existing tests | Lazy-load: materials panels not fetched until tab click |
| | No duplicate network call for layer confirmation (mock spy count) |

---

## 13. Următorul prompt recomandat

```text
BUILD: INTAKE_V3_OPERATOR_WORKSPACE_CLEANUP_PRE_PHASE2

Scope:
1. Commit docs/architecture/INTAKE_V3_OPERATOR_WORKSPACE_IMPLEMENTATION_ROADMAP.md
   + docs/audits/INTAKE_V2_VS_V3_OPERATOR_WORKSPACE_PRESENTATION_AUDIT.md
2. Remove LayerSetup duplicate fetch
3. Lazy-load production/quote panel fetches on first tab visit
4. Remove operator footer debug tab list
5. Add tests for lazy-load + single layer fetch
6. QA doc BUILD_INTAKE_V3_OPERATOR_WORKSPACE_CLEANUP_PRE_PHASE2.md

Boundary: frontend-only, no backend, no ColorRegistry yet.

Then:
BUILD: INTAKE_V3_OPERATOR_WORKSPACE_PHASE2_COLOR_REGISTRY
```

Optional parallel: **Playwright visual smoke** on `/operator` with seeded fixture (not blocking Phase 2).

---

## 14. Autoevaluare

| Criterion | Score | Note |
|-----------|-------|------|
| Corectitudine față de surse (git, cod, Atoms, roadmap, QA) | **8/10** | Inspecție statică; fără runtime browser pe workspace real |
| Respectarea arhitecturii WorkOS / roadmap | **8/10** | Phase 1 boundary respectat; lazy-load roadmap item missed |
| Risc de deviere (shell vs prod UX) | **6/10** | Moderat — cosmetizare panouri legacy poate masca gap-uri Phase 2–3 |

---

## Appendix: commit stats summary

| Range | Files | Lines |
|-------|-------|-------|
| `b4d8500..66ebd81` | 22 | +2249 |
| `66ebd81..1547367` | 18 | +874 / −389 |
| **Total operator workspace** | ~22 unique + 1 presentation | ~2730 net |

Phase 1.5 = **~40% reformat** of operator-workspace files, not second full rewrite.
