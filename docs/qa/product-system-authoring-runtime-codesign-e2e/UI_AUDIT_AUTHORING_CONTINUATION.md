# UI audit — Product System Authoring Continuation

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Route under audit | `/product-system/products/{code}` + `/product-system/blueprint-dossier` |
| Verdict | **NEEDS_POLISH** (improved coherence; not FINAL) |

## Sincere answers 1–14

| # | Question | Answer |
|---|----------|--------|
| 1 | Is there one clear authoring shell? | **Partial** — Products catalog + detail tabs now cover Overview→Publication; shell nav still has planned placeholders. |
| 2 | Can operator find composition editing? | **Yes** — Composition tab mounts `TemplateCompositionAuthoringPanel`. |
| 3 | Are contracts on the template route? | **Yes** — Contracts tab mounts `ComponentContractUsedByPanel`. |
| 4 | Dual BUILD vs TEMPLATE status visible? | **Yes** — `TemplateDualStatusChips` on detail header. |
| 5 | Badge noise reduced? | **Partial** — capability chip removed; commercial StatusBadge retained; dual chips are primary. |
| 6 | Dossier deep-link retains template? | **Yes** — `?template=` focus on Blueprint Dossier Studio. |
| 7 | Sticky Save→Validate→E2E→Publish? | **Yes** — footer actions present; Validate/E2E/Publish scroll to rails (do not auto-publish). |
| 8 | Readiness + Publication in real flow? | **Yes** — dedicated tabs + prior lifecycle mount. |
| 9 | Runtime Preview on template? | **Yes** — read-only PD progressive disclosure. |
| 10 | Fake Publication ready for VL? | **No** — Aluminiu inactive still blocks; UI must show BLOCKED. |
| 11 | Geometry inference in UI? | **No** — schema fields are inputs only. |
| 12 | Figma FINAL parity claimed? | **No** — frames remain NEEDS_POLISH / DESIGN_ONLY. |
| 13 | Mobile / sessions? | **Out of scope** — desktop admin authoring. |
| 14 | Overall UI PASS? | **No** — **NEEDS_POLISH**. Coherent enough for owner review; density/tab count still high. |

## Screenshot pack (continuation)

Live capture preferred when stack :3000/:8000 up. Without capture this gate: document **PARTIAL / ENVIRONMENT**.

Expected ids (do not invent Publication-ready VL):

1. Landing products
2. Template overview + dual chips
3. Composition authoring
4. Components
5. Contracts
6. Relationships
7. Materials / PD materials
8. Dossier tab CTA
9. Dossier Studio deep-link
10. Sticky footer Save/Validate/E2E/Publish
11. Runtime Preview
12. E2E Readiness (BUILD PASS / TEMPLATE BLOCKED)
13. Publication blocked
14–22. Prior pack reuse / Figma `91:3`…`91:100` classification shots

## Figma classification (no invented IDs)

| Frame | ID | Class |
|-------|-----|-------|
| Template Authoring Shell | `91:3` | NEEDS_POLISH |
| Component Contract | `91:12` | NEEDS_POLISH |
| Dossier Studio | `91:21` / `91:32` | NEEDS_POLISH |
| Publication | `91:36` | NEEDS_POLISH |
| Readiness | `91:60` | NEEDS_POLISH |
| Pack shells | `91:76`–`91:100` | DESIGN_ONLY |
| Intake Confirmare | `66:2` | FINAL (untouched) |
