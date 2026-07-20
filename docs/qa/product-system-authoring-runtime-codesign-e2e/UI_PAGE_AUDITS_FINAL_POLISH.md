# Complete-page audits — Product System UI Final Polish

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Kickoff HEAD | `2d4b348` |
| After polish | see final report HEAD |

## Visual order (target)

identity → lifecycle → composition/contracts → blockers → validation → readiness → publication → runtime preview → technical diagnostics

---

## `/product-system/products` (Landing)

| Axis | Before | After / should |
|------|--------|----------------|
| Dominates now | Catalog buckets + many chips | Products catalog still primary; shell subtitle clarifies flow |
| Duplicates | Shell “Product System” + page titles | Kept; Pricing Registry demoted to utility link |
| Noise | Planned nav badges compete | Planned remain visible but secondary (dashed / muted) |
| Hidden | Authoring path to VL detail | Unchanged — select product → detail |
| Too technical | Bucket jargon | Acceptable for admin; no fake offerability |
| Move/remove | — | No architecture change; subtitle added |

**Verdict:** improved shell clarity; landing remains catalog-first (correct).

---

## `/product-system/products/{code}` (Template authoring)

| Axis | Before | After / should |
|------|--------|----------------|
| Dominates | 11 equal purple pills + modularity wall + StatusBadge | Identity header + dual Build/Publicare chips; primary underline tabs; diagnostics secondary row |
| Duplicates | Components ≈ Composition list; Materials ≈ Runtime Preview | Components/Materials/Relationships → diagnostic row; Runtime Preview primary for PD |
| Noise | Capability/commercial badge + dual chips + modularity chips | Commercial StatusBadge under “Status catalog”; modularity in `<details>` |
| Hidden | Readiness/Publication were tabs but buried | Primary tab order: … Dossier → Readiness → Publicare → Runtime Preview |
| Too technical | Mono codes dominant | Human name primary, code secondary |
| Move/remove | Garduri → Diagnostic label | Diagnostics last |

**Verdict:** hierarchy matches target order; density reduced without removing authority surfaces.

---

## `/product-system/blueprint-dossier` (+ `?template=`)

| Axis | Before | After / should |
|------|--------|----------------|
| Dominates | Editor + violet sticky | Sticky command model RO: Salvează → Validează → Verifică → Publică |
| Duplicates | Publication/Readiness also on template tabs | Intentional dual mount (rail + template) — same honesty |
| Noise | English Validate/E2E/Publish | Romanian labels; slate (less violet dominance) |
| Hidden | Deep-link template focus | Preserved `?template=` |
| Too technical | Save≠Validate≠E2E≠Publish jargon | Kept as honesty string, RO phrasing |
| Move/remove | — | Footer a11y region label only |

**Verdict:** command model clearer for daily admin; authority unchanged.

---

## Families / Contracts / Preview / Readiness / Publication (distinct?)

| Surface | Distinct route? | Notes |
|---------|-----------------|-------|
| Families | No dedicated | Catalog buckets on Products |
| Contracts | Tab on template + dossier rail | Mounted; human used-by |
| Preview | Tab `runtime-preview` | Human summary + collapsed diagnostics |
| Readiness | Tab `readiness` (+ dossier) | Compact dual BUILD/TEMPLATE |
| Publication | Tab `publication` (+ dossier) | Blocked banner human-primary |

No new routes invented.

---

## Planned shell routes (`/components` … `/advanced`)

Honest “Planificat” placeholders — unchanged architecture; screenshot `polish_22` confirms.
