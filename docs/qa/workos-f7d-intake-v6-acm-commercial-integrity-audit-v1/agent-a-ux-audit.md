# Agent A — Intake V6 UX Audit (Full-Page Hierarchy, Friction, Progressive Disclosure)

Scope note per mission boundary: this is analysis and **proposals only — no implementation**. All findings are cross-referenced to the live-tested workspace `5a5ce742-f50f-47b0-985b-32cc6f2fb6a4` and fixture `test-bond-litere.svg`. Detailed field-level evidence is in [`agent-a-field-ledger.md`](./agent-a-field-ledger.md) and [`agent-a-acm-bond-matrix.md`](./agent-a-acm-bond-matrix.md); this document is the page/interaction-level view.

---

## 1. Full-page hierarchy as experienced live

```
Intake V6 Operator Workspace (/intake-v6-app/{id}/operator)
│
├── Step 1 — Straturi                                    [progress: "Pasul 1 din 3"]
│   ├── Card: Fișier recunoscut
│   │   ├── thumbnail preview + dimensiune/straturi/culori/contururi chips
│   │   └── actions: Deschide preview · Schimbă fișier
│   ├── Card: Decizii straturi (repeats per detected <g> layer — 2× here)
│   │   ├── Rol geometrie (select)
│   │   ├── Detalii tehnice (collapsible)
│   │   └── Componentă produs chip (auto, read-only)
│   ├── Card: Compoziție produs (collapsible, auto-expanded once roles picked)
│   │   ├── 2 component chips ("Inclus în propunere" ×2, but different real status)
│   │   ├── Detalii tehnice compoziție (collapsible — legacy template note)
│   │   └── action: Confirmă (single button confirms BOTH components at once)
│   ├── Card: Ce producem? (4-way scope segmented control)
│   ├── Card: Metrici tehnice & geometrie (collapsible)
│   └── Right rail: Panou operator (upload state, straturi progress ring, "Toate straturile confirmate" pill)
│   └── Footer: "N blocante · N informații" strip (collapsible, spans full width)
│
├── Step 2 — Configurare                                  [progress: "Pasul 2 din 3"]
│   ├── Tab bar (4 tabs, always visible, each with its own sub-label)
│   │   ├── Finisaje (Față · cant · Vector Logo)
│   │   │   └── per-element card × N elements
│   │   │       ├── Fața (Finisaj, Rolă, Culoare) — nested combobox + swatch grid
│   │   │       ├── Cant (Finisaj, Adâncime, Culoare RAL) — nested combobox + swatch grid
│   │   │       ├── Spate (Mod)
│   │   │       └── Detalii tehnice despre finisaj (collapsible — raw token leak, see §3)
│   │   ├── Iluminare și surse LED
│   │   │   └── LED activ · Tip · Culoare · Putere · Sursă · Rezultate calculate (read-only)
│   │   ├── Panou / carcasă (ACM core — see dedicated matrix)
│   │   │   └── Previzualizare · Rezumat · Geometrie · Construcție · Segmente · Material/finisaj
│   │   │       · Structură și montaj · Relații · Detalii tehnice (raw JSON) · Avansat (3 sub-fields)
│   │   │       · Confirmă panoul Alucobond (single commit action)
│   │   └── Montaj comercial (Scope · șablon · șantier)
│   ├── (repeated on every tab) Ajustări comerciale block — Adaos % / Discount % / TVA % / Ajustare RON
│   ├── Right rail: Ofertă client
│   │   ├── Estimare provizorie — panou Alucobond (only visible while on Panou/carcasă tab)
│   │   ├── Estimări pe produs (Litere €, Panou Alucobond €, Legături Litere↔Bond)
│   │   ├── Detalii panou (N) — collapsible line-item breakdown
│   │   ├── Detalii linii (N) — collapsible full line breakdown
│   │   └── Ce blochează (blocker summary)
│   └── Footer: "N blocant(e) · N informații" strip (same pattern as Step 1)
│
└── Step 3 — Confirmare                                    [progress: "Pasul 3 din 3"]
    ├── Checklist: Compoziție produs confirmată / Finisaje confirmate (read-only, auto-ticked)
    ├── Checkbox: Confirm finisajele și datele de ofertare pentru draft intern (the real blocker)
    ├── Recapitulare și diagnostic tehnic (3-card summary — letters only, no ACM, see Finding P0)
    ├── Ofertă client total (Net/TVA/Adaos rollup)
    └── action: Creează oferta prețuită / Continuă către ofertă (NOT executed — out of boundary)
```

**Observation on hierarchy itself:** the three steps are well-separated and the progress model ("Pasul N din 3") is honest and legible. The strain is **inside** Step 2 — one tab (Panou/carcasă) alone contains 9 distinct sub-sections, more than the other three tabs combined, and it is the tab an operator must visit for any ACM/Bond job. This is a natural consequence of the ACM panel being the most complex product in the catalog, but it means the "4 equal tabs" mental model breaks down in practice — one tab is really "3-4 tabs' worth" of decisions compressed into one scroll.

---

## 2. Friction / click-count analysis (as walked live, ACM+Letters fixture)

| Task | Clicks/inputs observed | Friction notes |
|---|---|---|
| Upload SVG → both layer roles proposed | 1 (upload) | AI proposal was correct for both layers zero-shot; no friction here. |
| Confirm both layer roles | 2 (one per layer) + could be 1 via "Confirmă toate sugestiile" | Good accelerator exists and was used. |
| Confirm product composition | 1 | **But this 1 click silently accepts the optional ACM panel's "available_optional" status without ever asking "do you want the panel in this offer?" as a distinct yes/no** — the only signal is a chip label whose exact wording is ambiguous (see Finding P0 in JSON summary). |
| Reach the ACM configuration tab | 1 (tab click) | Direct — no friction. |
| Confirm the ACM panel (geometry+construction+finish) | 1 ("Confirmă panoul Alucobond"), after reviewing 5 pre-filled catalog-default fields | This is a genuinely good pattern: one commit, not 5 separate confirms. But because the 5 fields arrive as catalog guesses rather than derived-from-artwork facts, the operator's real task is "silently trust 5 defaults or manually verify each one against a paper spec" — the UI does not make trusting vs. verifying feel like a deliberate choice, it is bundled together. |
| Understand whether the ACM panel is priced into the current total | **effectively unbounded** — required cross-referencing 4 different UI locations (Step 1 footer warning, Step 1 composition chip, Step 2 right rail, Step 3 recap) to resolve, and even after resolving it, no single screen states the true answer for both an "as of right now" and "was this decision confirmed" perspective simultaneously | This is the audit's single worst friction point — see Finding P0. |
| Reach Step 3 and understand the final commercial recap | 1 click ("Continuă la Confirmare"), then must expand the Recapitulare card | The recap card is collapsed by default and is the **only** place a "one glance, am I about to price the right thing" check would happen — yet it omits the ACM panel entirely. |

**Overall click efficiency verdict:** the *technical* configuration path (upload → roles → composition → geometry/construction/finish → confirm) is efficient and well-accelerated (batch-confirm buttons, live recompute, autosave). The *commercial-clarity* path (does the operator know what they are about to price) requires materially more effort than the technical path and is the actual bottleneck.

---

## 3. Progressive disclosure — problems found (not fixed, per boundary)

### 3.1 Everything-expanded-by-default on the ACM tab
The Panou/carcasă tab shows Geometrie, Construcție panou, Material și finisaj, and Structură și montaj all expanded simultaneously on first arrival (only Segmente, Relații, Detalii tehnice, and Avansat start collapsed). For a first-time operator this is a wall of ~15 visible inputs before any scrolling context is established. **Proposal (not implemented):** collapse Construcție panou and Material și finisaj by default until Geometrie is confirmed once, matching the sequencing that's already implied by the tab's own subtitle ("Geometrie · suport · L1/L2").

### 3.2 Diagnostic-grade content mixed into operator-grade collapsibles
Three different collapsible sections use the exact same visual affordance (a `▸ Label` disclosure triangle) for wildly different audiences:
- "Detalii tehnice" (per layer, Step 1) — thin, operator-appropriate (template code only)
- "Detalii tehnice" (ACM panel, Step 2) — a raw pretty-printed JSON object with internal field names
- "Detalii atelier" (ACM material/finish) — workshop-facing, appropriately technical but still operator-adjacent

Because all three look identical when collapsed, an operator has no way to predict which ones are safe to casually open versus which one will show them a JSON blob. **Proposal:** a visually distinct affordance (e.g. a "diagnostic" tag or different icon) for panels whose content is genuinely developer/QA-facing (the raw JSON dump, the `canonical_unresolved_warning:*` strings, the "Ownership: MOUNTING → …" paragraph), separate from panels that are legitimately deeper operator detail.

### 3.3 The commercial-adjustment block should not be per-tab content
`Adaos comercial % / Discount % / TVA % / Ajustare manuală` is identical, global, workspace-level commercial state — yet it is rendered as if it were tab-scoped content, repeated 4 times (once per Configurare tab). This isn't just a duplication smell (already flagged in the field ledger); from a progressive-disclosure standpoint it also means these controls compete for visual priority against genuinely tab-specific decisions on every single tab, all the time, whether or not the operator is currently thinking about pricing adjustments. **Proposal:** hoist to a single persistent location (e.g. always-visible in the right rail, already home to "Ofertă client") rather than duplicated inside the tab body.

### 3.4 The ACM "blocker" list is shown twice before it can be acted on
The 5 catalog-default fields (Pliuri, Grosime, Pliu 1, Pliu 2, and the implied "Adâncime casetă") are listed once in the top-of-tab blocker summary and then immediately again as the live form below. Progressive disclosure normally means *revealing detail on demand*; here the same facts are disclosed twice in immediate succession with no additional information gained on the second viewing. **Proposal:** make the blocker-list line items scroll-to-anchor into the actual field below on click (if not already wired) rather than duplicating the value/state a second time in the list itself.

### 3.5 The Step 3 recap is the one place operators most need progressive disclosure to fail open, not closed
Every other collapsible in this app defaults to a reasonable state for its risk level — except the single highest-stakes screen (final recap before creating a priced offer), where the recap card requires an explicit expand and, even expanded, omits the ACM panel. **Proposal:** the final recap should default to expanded and should be schema-driven off the same "applied_content" / composition-confirmed list used in Step 1, so it can never silently omit a component that is priced into the total.

---

## 4. What is genuinely good (for balance, and to avoid "fix what isn't broken")

- Live recompute (LED module count, PSU sizing, ACM priced-line rollup) with no save/reload step.
- Honest "stale but inactive" messaging on the Montaj comercial tab (mounting template kept in data but explicitly marked inactive when scope is "none") — this is the pattern the recap card and the composition chip should be following but currently are not.
- Single-commit confirm actions ("Confirmă panoul Alucobond", the step-3 checkbox) instead of many small saves — reduces the chance of a half-configured component reaching pricing.
- AI layer-role proposal was 100% correct for this fixture zero-shot, meaning the single most error-prone step (mapping arbitrary CorelDRAW layer names to product roles) currently costs the operator almost nothing.
- VAT is correctly locked/readonly rather than left editable.

---

## 5. Summary for Lead / Agent B handoff

The structural hierarchy (3 steps, 4 tabs) is sound and the technical configuration experience is efficient. The concentration of complexity on the single ACM/Bond tab is proportionate to that product's real complexity, not a design mistake — but three specific patterns (raw internal strings surfacing in operator collapsibles, per-tab duplication of global commercial controls, and a final recap that both defaults-collapsed and omits a priced component) are the actionable, narrowly-scoped UX debt this audit identified. None of these require the redesign this mission's boundary forbids; each is a targeted fix to an existing component.
