# Git History and Ownership Trace

**Tools:** local `git` (primary) + `gh` CLI authenticated as `office952`.  
**GitHub MCP:** not installed.  
**PR for branch head:** none (`gh pr list --head feature/product-system-active-path-isolation-v1` → `[]`).

| Path/field | Introduced commit | Major later changes | Current owner | Historical conflict? | Verdict |
|------------|-------------------|---------------------|---------------|----------------------|---------|
| `mounting_scope` / mountingScope | `6bdfb48` Intake V6 mounting scope foundation | `b4124a5` immediate save; `c0a3404` decouple ACP from scope; fixing wave | Commercial mounting service + FE `mountingScope.ts` | Legacy scopes in same keys | Live |
| `mounting_solution` | `f6dbb84` Link mounting prep to Product System | ACM boxed wave `564ce48`…; SVG dims; `5336734` UI | Product System template ref OR installation_template | Dual kind under one field | Live dual-meaning |
| Montaj cluster shell | `fc9c21b` realign page two operator flow | vocab `bfddb1e`; composition `5336734` | FE ReviewStep / shells | Product+commercial under one tab | Structural mix |
| `mounting_fixing_system` | `1334c9c` / `8069a4c` | `76d7206` | ACP fixing contract | separate from scope (intentional) | Live |
| Finish/mounting ownership contracts | `55de354` | `4229940` decouple | Product ownership docs/UI | Docs vs Intake tab packaging | Parallel product surface |
| `mains_cable_length_m` / service_corner | `6fe5c50` process resolver | typed fields `4ccfba6`; CPP electrical; UI packaging `fc9c21b` | Process resolver + FinishSetup | Backend first, UI later | Live |
| `mounting_template_*` | baseline `1f9fda1` / reused `6bdfb48` | pricing CPP; Forex tasks | Commercial template | Long-lived key reused | Live |
| Segmented ACM | `7eaa093` contracts | confirm `41129b6`/`bf2df42`; electrical `7f3e507`; UI `fc9c21b`…`5336734` | `acm_segmented_*_service` | Unpriced by design | Live |
| Desktop composition V2 | `5336734` | hash note `abb30b7` | FE presentation only | Does not fix Montaj truth split | Presentation candidate |

## Abandoned / parallel leftovers

- Legacy `mounting_system` / `mounting_bar_profile` still readable in PD/pricing fallbacks after solution canonicalization (`f6dbb84` era).
- `svg_support_selection` dual with SUPPORT_CONTOUR bindings (adapter, not dead).
- Docs drift: `ACP_INTERNAL_FRAME_SOURCE_MAP.md` vs current nested frame UI (stale doc risk).

## Authority note

History from `git log` / `-S` searches — not from code comments alone.
