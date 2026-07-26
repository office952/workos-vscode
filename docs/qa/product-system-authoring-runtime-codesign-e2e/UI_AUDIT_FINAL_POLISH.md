# UI audit — Product System UI / Figma Final Polish

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Routes | `/product-system/products`, `/products/{code}`, `/blueprint-dossier` |
| Verdict UI | **PASS_WITH_WARNINGS** (usable daily admin; not pixel-FINAL) |
| Verdict Figma | **NEEDS_POLISH** (no FINAL promotion) |

## Sincere answers 1–14

| # | Question | Answer |
|---|----------|--------|
| 1 | One clear authoring shell? | **Yes, improved** — Products + template primary tabs; planned nav honest. |
| 2 | Find composition editing? | **Yes** — Compoziție primary tab; soft include/role first. |
| 3 | Contracts on template route? | **Yes** — Contracte primary; used-by human-primary. |
| 4 | Dual BUILD vs TEMPLATE visible? | **Yes** — chips + readiness dual axes (compact). |
| 5 | Badge noise reduced? | **Yes** — commercial badge under details; dual chips primary. |
| 6 | Dossier deep-link keeps template? | **Yes** — `?template=` + sticky RO commands. |
| 7 | Sticky Save→Validate→Check→Publish? | **Yes** — Salvează → Validează → Verifică → Publică. |
| 8 | Readiness + Publication in real flow? | **Yes** — primary tabs; blocked honesty preserved. |
| 9 | Runtime Preview human-first? | **Yes** — rezumat operator; diagnostics collapsed. |
| 10 | Fake Publication ready for VL? | **No** — Aluminiu still blocks; screenshots prove. |
| 11 | Geometry inference in UI? | **No**. |
| 12 | Figma FINAL parity claimed? | **No** — frames NEEDS_POLISH / DESIGN_ONLY. |
| 13 | Mobile / sessions? | **Out of scope**. |
| 14 | Overall UI PASS? | **PASS_WITH_WARNINGS** — coherent for daily admin; Figma not FINAL; some catalog density remains. |

## Accessibility (spot)

| Check | Result |
|-------|--------|
| Tablists labeled | Yes (primary + diagnostic) |
| Dual chips aria-label | Yes |
| Sticky footer region | Yes |
| Keyboard tab buttons | Native `<button role="tab">` |
| Color-only status | No — text labels on chips |
| Focus / contrast | Acceptable on dark admin; not WCAG-certified this gate |

## Screenshot pack

`polish_01`…`polish_23` captured live FE:3000 / evidence JSON — see inventory.
