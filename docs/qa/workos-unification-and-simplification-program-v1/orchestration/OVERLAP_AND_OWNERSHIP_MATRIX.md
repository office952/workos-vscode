# Overlap and ownership matrix

**Canonical page-card owner rule:** exactly one primary lane (or Wave 1) per route. Cross-cutting lanes are observers. Orchestrator synthesizes; reviewer challenges.

| Route / surface | Primary | F UI | G Legacy | H Nav | Notes |
|-----------------|---------|------|----------|-------|-------|
| AppShell chrome | Wave 1 | observe | observe | observe | Do not re-own |
| `/dashboard` | Wave 1 | observe | observe | observe | Preview honesty already logged |
| `/quotes` · `/quotes/:id` | Wave 1 | observe | observe | observe | A may add order-handoff notes only |
| `/shop-floor` | Wave 1 | observe | observe | observe | B observes production home |
| `/intake` · `/intake/:id` | **A** | observe | V4 residue | observe | |
| `/intake-v6/**` · standalone app | **A** | observe (hard-coded dark) | V4-in-V6 | observe | Deep workspace |
| `/orders` · `/orders/:id` | **A** | observe | observe | observe | |
| `/clients` · `/clients/:name` | **A** | observe | observe | observe | Commercial counterparty |
| `/execution/**` · `/operator` · `/tablet/**` | **B** | observe | compat primary for `/operator` `/tablet` | observe | G classifies; B still owns the page card |
| `/employee-app/**` | **B** | observe (no ThemeContext) | observe | observe | Standalone |
| `/employees*` · `/attendance*` · payments · advances | **C** | observe | observe | observe | Not lane E |
| `/product-system/**` · `/modules` · `/governance` | **D** | observe | lab/planned | observe | Not lane A despite Lucrări nav |
| `/inventory*` · `/utilaje` · `/settings` · `/documents` · `/colaboratori` · `/reports*` | **E** | observe | registry jargon | observe | Machine **runs** stay B |
| `/demo/**` | **D** or **E** per demo | observe | **G** classify | observe | Commercial-spine demo → E; volumetric → D |

## Cross-cutting rule

- **F** never owns a page card. Writes pattern / hardcoded / light-dark rows keyed by route.
- **G** never owns a page card. Writes classify rows. Compat routes still have a primary (usually B).
- **H** never owns a page card. Writes edges and journeys keyed by `FROM_ROUTE` / `TO_ROUTE`.
- If two primaries collide, **stop** and ask Owner. Do not dual-own.

## Observer protocol

Observer may add `lanes/<ID>/observations/<route>.md` pointing at the primary card. Must not duplicate the card. Orchestrator merges; contradictions go to `CONTRADICTION_LOG`.
