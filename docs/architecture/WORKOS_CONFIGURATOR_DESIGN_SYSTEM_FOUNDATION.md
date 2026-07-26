# WorkOS Configurator Design System Foundation

> **AUDIT + PROPOSAL ONLY** · **NO IMPLEMENTATION**  
> Date: 2026-07-19 · Branch: `feature/product-system-active-path-isolation-v1` · Baseline: `ac6e872`  
> Pilot: Intake V6 · Runtime remains acceptance truth  
> Evidence: `docs/architecture/assets/workos-configurator-design-system-foundation-2026-07-19/`

---

## 1. Executive summary

Intake V6 has a **stable functional and guidance foundation** (labels, status semantics, guidance spine, confirmation honesty, count consolidation). The remaining gap is **product feel**: the UI still reads as a dense ERP console rather than a premium product configurator.

This document defines the **WorkOS Configurator Design Language** before any visual redesign. Intake V6 is the **pilot**, not an exception. Structure (3 steps × 3 tabs × Montaj IA) stays frozen; what changes later is **presentation hierarchy, density, and disclosure**.

**Core shift**

```text
Wrong:  Backend object → Card → Accordion → Fields
Right:  Physical product → Operator decisions → System results → Validation → Confirmation
```

---

## 2. Current UI problems (Intake V6 pilot)

Sourced from runtime (`:3001` / `:8003`), journey review, count consolidation evidence, and `v6` presentation tokens.

| Problem | Evidence | Impact |
|---------|----------|--------|
| Tiny ERP typography | Page base `text-[12px]`; helpers `text-[11px]`; many panels `text-[10px]` | Hard to scan; feels like admin tooling |
| Flat hierarchy | Many equal-weight cards (composition, scope, sticky, tabs, pricing) | No clear “where am I deciding?” |
| Technical leakage on L1 | `TPL-*`, `authority live`, `legacy/deprecated`, English contract lines | Operator trust drop |
| Nested ownership cards | Card → compact card → accordion → more cards | Cognitive nesting tax |
| Inputs mixed with results | LED counts / PSU / pricing beside editable finishes | Unclear what to touch |
| Diagnostics as peers | Sticky + drawer + pricing warnings + technical accordions | Competing attention |
| Large empty + dense text | Wide grids + 10–11px rows | Feels unfinished and cramped at once |
| Weak product silhouette | Față/Cant/Spate as form rows, not a product diagram | Manufacturing mental model underused |
| Icon poverty | Sparse Lucide; most clusters text-only | Weak visual anchors |
| Pricing always-on | Live calc rail during Finisaje/Iluminare | Commercial noise during product truth |

**What is already good (do not undo)**

- Frozen IA: Straturi → Configurare (Finisaje / Iluminare / Montaj) → Confirmare  
- Operator status vocabulary (8 terms)  
- Guidance spine (footer primary action + sticky counts + drawer inventory)  
- Montaj order: Fundal → Segmentare → 220V → Comercial demoted  
- Display labels for Element / Față / Cant / Spate  

---

## 3. Design principles

1. **Manufacturing-first** — UI mirrors how the product is built, not how the API is shaped.  
2. **One decision at a time** — Level-1 viewport answers: what am I configuring now?  
3. **Decide → see result → validate** — never present calculations as editable fields.  
4. **Guidance is one language** — footer = action; sticky = attention; drawer = inventory (already established).  
5. **Technical truth is opt-in** — Detalii tehnice / Avansat / diagnostic — never first paint.  
6. **Romanian operator labels** — `WORKOS_UI_TERMINOLOGY_REGISTRY` + Intake V6 vocabulary.  
7. **Pilot, then systemize** — Intake V6 proves patterns; Product System / Quotes reuse later.  
8. **No beauty before meaning** — visual polish only after disclosure and hierarchy rules are accepted.

---

## 4. Operator mental model

| Operator thinks | UI must show | UI must hide |
|-----------------|--------------|--------------|
| What are we making? | Product silhouette + composition | Template IDs |
| What do I choose? | Material, color, LED type, mounting | Analyzer internals |
| What did the system compute? | Module count, PSU, areas | Raw enums |
| Can I continue? | Blocant / Avertizare + next action | Parallel banners |
| Am I done? | Confirmat / Pregătit | False ✓ on unfinished steps |

Persona: production estimator — materials, LED, casings, mounting. Not PD / Aggregate / contracts.

---

## 5. Page anatomy (configurator)

```text
┌ Shell (nav) ─────────────────────────────────────────────┐
│ Header: job id · product name · step progress            │
├──────────────────────────────────────────────────────────┤
│ L1 Product strip (optional): silhouette / composition    │
│ L1 Attention sticky (only if blockers/warnings)          │
├─────────────────────────────┬────────────────────────────┤
│ L2 Active cluster (tabs)    │ L3 Results rail (demoted)  │
│  Decision groups            │  Calculated / commercial   │
│  Primary controls           │  Collapsed by default on   │
│                             │  decision-heavy steps      │
├─────────────────────────────┴────────────────────────────┤
│ Footer guidance spine: status · progress · next action   │
│ Drawer: Blocante / Avertizări / Informații               │
└──────────────────────────────────────────────────────────┘
```

**Levels (max 4)**

| Level | Role | Example |
|-------|------|---------|
| L1 | Product / major section | Configurare · Finisaje |
| L2 | Functional cluster | Față · Cant · Spate |
| L3 | Decision group | Material + color fields |
| L4 | Technical details | Ownership tokens, IDs |

Unlimited nesting is forbidden.

---

## 6. Typography system (proposal)

Current tokens (`intakeV6Presentation.tsx`): page `12px`, screen title `15px`, section `14px`, helpers `11px`, badges `11px`. Too small for a configurator.

| Role | Proposed size | Weight | Notes |
|------|---------------|--------|-------|
| Page / screen title | 20–22px | Semibold | Hero of the step |
| Section title | 16–18px | Semibold | Finisaje, Montaj cluster |
| Card / decision title | 14–15px | Semibold | Față, Segmentare |
| Field label | 13px | Medium | Never below 12px |
| Body / control value | 14px | Regular | Inputs readable |
| Helper | 12–13px | Regular | Secondary |
| Technical / mono | 11–12px | Mono | **Only L4** |
| Metric / result value | 16–18px | Semibold | Calculated outputs |

**Rule:** Prefer fewer sizes. Avoid `text-[10px]` on operator surfaces.

---

## 7. Spacing system (proposal)

| Token | Proposal | Role |
|-------|----------|------|
| Page margin | 24–32px | Breathing room |
| Section gap | 24px | Between L1/L2 |
| Card padding | 16–20px | Decision blocks |
| Field gap | 12–16px | Within group |
| Cluster gap | 16px | Between Față/Cant |

Goal: more air without dashboard sprawl. Dense tables only in L4 / Confirmare summaries.

---

## 8. Card rules

| Pattern | Use when | Avoid when |
|---------|----------|------------|
| **Section** | Named cluster with one job | Wrapping everything |
| **Card** | One decision group or one result group | Nesting cards 3+ deep |
| **Accordion** | L4 technical / optional | Hiding the primary decision |
| **Table** | Many homogeneous rows (layers, BOM lines) | Single decision |
| **Inline field group** | 2–4 related inputs | Mixing inputs + calc |

**Allowed nesting**

```text
Section
 └ Decision block (card)
     └ Fields
```

**Forbidden**

```text
Card → Card → Card → Accordion → Card
```

---

## 9. Product representation rules

UI should show **physical construction**, not template ownership.

### Volumetric letters (pilot)

| Part | Operator sees | Decision | Result |
|------|---------------|----------|--------|
| Față | Face plane | Material / finish / color | Area, film |
| Cant | Return/side | Depth, finish | Perimeter |
| Spate | Back | Mode (Forex…) | Backing |
| Iluminare | Light path | LED type | Modules, PSU |
| Fixare / Montaj | How it mounts | Structure / site | Fasteners later |

### ACM/ACP casing

| Part | Operator sees |
|------|---------------|
| Față | Face panel |
| Pereți | Walls |
| Cadru | Frame |
| Spate | Back |
| Electrică | 220V feed (after structure confirmed) |

**Visual aid (future implementation):** a small exploded/schematic silhouette beside the active cluster — not a decorative hero image.

---

## 10. Input / result rules

| Kind | Presentation | Editable? |
|------|--------------|-----------|
| **Input** | Control (select, number, confirm) | Yes |
| **Result** | Read-only metric / chip | No |
| **Proposal** | Status Propunere + Confirmă/Respinge | Confirm only |
| **Diagnostic** | L4 accordion | No |

Never style a calculated value like an input. Never place pricing totals as Level-1 competitors to unfinished product decisions.

---

## 11. Status rules

Canonical vocabulary (frozen):

Propunere · Necesită confirmare · Lipsă date · Avertizare · Blocant · Decizie administrator · Confirmat · Pregătit

| Status | Visual treatment (proposal) |
|--------|------------------------------|
| Propunere | Amber outline chip |
| Necesită confirmare | Amber filled chip |
| Lipsă date | Neutral + dashed affordance |
| Avertizare | Amber border block (non-blocking) |
| Blocant | Rose border sticky / list item |
| Decizie administrator | Distinct violet/slate chip (not “error”) |
| Confirmat | Emerald chip |
| Pregătit | Emerald / sky “ready” aggregate |

Guidance counts stay: Blocante / Avertizări / Informații (count consolidation).

---

## 12. Iconography rules

Icons are **anchors**, not decoration.

| Domain | Suggested metaphor |
|--------|--------------------|
| Material / finish | Layers / swatch |
| Iluminare | Lightbulb |
| Electrică | Zap / plug |
| Montaj / fundal | Box / panel |
| Dimensions | Ruler |
| Validation | Alert / check |

**Style:** outlined Lucide-compatible set, 16–20px, one weight, no emoji, no glow stacks. One icon per L2 cluster title; not every field.

---

## 13. Blocker presentation rules

A blocker must answer four questions in one place:

| Question | Surface |
|----------|---------|
| What? | Short RO message |
| Why? | One clause (optional) |
| Where? | Destination (Finisaje / Montaj / …) |
| Action? | Footer **Următorul pas** |

Sticky = counts only. Drawer = inventory. Footer = single next action. No parallel “primary” paragraphs.

---

## 14. Technical disclosure rules

| Visible on L1/L2 | Move to L4 / Avansat / diagnostic |
|------------------|-----------------------------------|
| Față, Cant, Spate | `TPL-*` codes |
| Necesită confirmare | `authority live`, FinishSetup |
| Confirmă compoziția | Product Truth / Aggregate |
| LED modules (result) | Contract English strings |
| Segmentare Propunere | Contour hashes, analyzer IDs |

**Never again on first level:** raw enums, UUID primary labels, “legacy/deprecated” as primary copy, English modular-form sentences.

---

## 15. Component patterns (canonical candidates)

Extend `v6` tokens into a **Configurator kit** (future implementation):

| Pattern | Purpose |
|---------|---------|
| `ConfiguratorPage` | Shell + margins + title scale |
| `ProductStrip` | Silhouette + composition summary |
| `DecisionCluster` | L2 section with icon + title |
| `DecisionCard` | L3 inputs only |
| `ResultPanel` | Read-only metrics |
| `StatusChip` | Vocabulary tones |
| `AttentionSticky` | Count summary |
| `GuidanceFooter` | Spine (already exists conceptually) |
| `TechnicalDisclosure` | Accordion L4 |

Existing `AtomsBadge` tones (`ok/pending/action/muted`) must map to the 8 status terms — today they are incomplete.

---

## 16. Intake V6 pilot recommendations (post–owner GO)

Ordered; **no implementation in this audit**.

1. **Typography uplift** — raise base from 12→14px; kill 10px on operator surfaces.  
2. **Product strip** — Față/Cant/Spate/Iluminare silhouette above tabs.  
3. **Demote pricing rail** on Finisaje/Iluminare until Confirmare (or collapse by default).  
4. **Composition L1 cleanup** — keep Confirmă; hide TPL/legacy behind Detalii tehnice.  
5. **Decision vs Result split** in Iluminare (inputs left, modules/PSU right as results).  
6. **Icon pack** on three tabs + Montaj clusters.  
7. **Card nesting audit** — flatten one level in Finisaje/Montaj.  
8. **Only then** Figma refresh to match runtime + new tokens.

---

## 17. What must never happen again

- Designing cards from backend ownership trees  
- Showing template codes as primary identity  
- Mixing editable inputs with calculated values styled as inputs  
- Adding a fourth parallel warning channel  
- False completion ✓ on unfinished Configurare  
- “Probleme — N” without severity breakdown  
- Visual polish that reopens Montaj/contracts/domain  

---

## 18. Migration approach

```text
Phase 0  Foundation accepted (this doc)     ← now
Phase 1  Token + typography pilot (Intake)  ← owner GO
Phase 2  Product strip + input/result split
Phase 3  Disclosure sweep (TPL/technical)
Phase 4  Figma sync (design follows runtime)
Phase 5  Reuse kit on Product System / Quotes
```

Each phase: presentation only unless owner opens domain.

---

## 19. Owner decisions (required)

| ID | Decision | Options |
|----|----------|---------|
| OD-DS-01 | Accept design principles §3? | Accept / Amend |
| OD-DS-02 | Typography scale §6 as target? | Accept / Amend sizes |
| OD-DS-03 | Pricing rail default-collapsed on Configurare? | Yes / No / Confirmare-only |
| OD-DS-04 | Product silhouette required on pilot? | Yes / Later |
| OD-DS-05 | First implementation build after GO? | Typography uplift / Product strip / Disclosure sweep |

---

## 20. Design tokens audit (current)

From `frontend/src/components/workos/intake-v6/atoms/intakeV6Presentation.tsx`:

| Token | Current | Conflict |
|-------|---------|----------|
| `page` | `#0A0F1A`, `12px` | Too small for configurator |
| `card` / `cardCompact` | `#111827`, 10px radius | Overused → nesting |
| `screenTitle` | 15px | Should be ~20–22px |
| `sectionTitle` | 14px | Slightly low |
| `helper` / `metricLabel` | 11px | Borderline |
| `input` / buttons | 12px | Raise with body |
| `AtomsBadge` | 4 tones | Incomplete vs 8 statuses |
| Colors | sky / emerald / amber / rose / slate | Keep; map to status rules |

Many components bypass `v6` with one-off `text-[10px]` — that is the density problem.

---

## 21. Marketplace / tool research (no install)

| Tool | Usefulness | Permissions | Overlap | Recommendation |
|------|------------|-------------|---------|----------------|
| **Figma MCP** (present) | Read designs, compare to runtime | Already connected | High for audit | **Keep for audit**; do not push redesign until Phase 4 |
| **Storybook** | Component catalog for configurator kit | Would need setup | Medium | **Later** after tokens exist |
| **Visual regression (Playwright/Chromatic)** | Catch density regressions | CI change | Medium | **Later** with Phase 1 |
| **axe / a11y** | Contrast after type uplift | Dev dep | Low | Useful in Phase 1 |
| **Browser MCP** | Runtime screenshots | Present | High | **Keep** as acceptance evidence |
| Extra UI kits / themes | Tempting shortcuts | Install risk | High conflict | **Do not install** |

Do not recommend a marketplace shopping list. One design language first.

---

## 22. Figma audit (read-only)

| Item | Finding |
|------|---------|
| Primary file | `0CDPIuqoaZ1OQgNnvNyl1F` — Configurare UI/UX Polish |
| Frames | FINAL Finisaje / Iluminare / Montaj / Confirmare @ 1440×900 |
| Age | Pre–segmented electrical / pre–guidance spine / pre–count consolidation |
| Drift | Figma still useful for shell/tab chrome; runtime IA and guidance are ahead |
| Secondary | `911Q6oRKcEursrRoT4Qj0h` — older UI/UX audit frames |
| Rule | **Do not update Figma in this task.** Runtime = acceptance truth. Sync only after owner GO on Phase 4. |

---

## 23. Related authorities

- `docs/qa/intake-v6-ui-foundation-baseline-2026-07-19/` — frozen IA  
- `docs/qa/intake-v6-operator-journey-review-2026-07-19/` — experience gaps  
- `docs/qa/intake-v6-configuration-guidance-spine-2026-07-19/` — action spine  
- `docs/qa/intake-v6-count-channel-consolidation-2026-07-19/` — count model  
- `docs/architecture/WORKOS_UI_TERMINOLOGY_REGISTRY.md` — RO labels  
- `docs/architecture/WORKOS_PAGE_COMPLETION_FOUNDATION.md` — page DoD / Figma policy  

---

## 24. Screenshots (current runtime)

| File | Surface |
|------|---------|
| `assets/workos-configurator-design-system-foundation-2026-07-19/01_configurare_current.png` | Configurare + guidance |
| `…/02_page1_current.png` | Straturi |
| `…/03_finisaje_current.png` | Finisaje |
| `…/04_iluminare_current.png` | Iluminare |
| `…/05_montaj_current.png` | Montaj / Fundal |
| `…/06_confirmare_current.png` | Confirmare |

---

**End of foundation proposal. Implementation only after owner GO on OD-DS-01…05.**
