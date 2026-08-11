# READ_MODEL_COST_AND_VALUE_MAP

Step 2 Configurare @ `303add0f`

| Read model | Why | Visible Step 2? | Needed before Confirm? | Affects offer? | Duplicate? | Class |
|------------|-----|-----------------|------------------------|----------------|------------|-------|
| Workspace / finish_setup | Form truth | Yes | Yes | Yes | — | CRITICAL |
| Company commercial settings | VAT/FX | Indirect | Yes | Yes | — | CRITICAL |
| Template form contract | Options | Yes | Yes | Indirect | Partial vs modular | CRITICAL |
| Modular form contract | Tabs/labels | Yes | Yes | Indirect | Partial | CRITICAL |
| Product system binding | Template/modules | Partial | Yes | Indirect | payload.product_binding | CRITICAL |
| Product definition preview | Composition segments | Sheet only | Nice | No | Binding | SECONDARY |
| Material breakdown | Cost/blockers | Rail + drawer | Yes | Yes | vs logical list | CRITICAL |
| Logical list | Material rows | Rail | Yes | Display/ACM | vs breakdown | CRITICAL (costly 322ms) |
| Pricing input preview | Slider defaults | Yes | Yes | Yes | vs dry-run | CRITICAL |
| Priced quote dry-run | Official Ofertă | Rail | **Yes** | **Yes** | Spine re-fetch | CRITICAL |
| Face/back prep draft | CNC cost line | Rail/drawer | Helpful | Yes | — | CRITICAL |
| Quote handoff preview | Blockers/readiness | Banner/header | **Yes** | Indirect | readiness_status | CRITICAL |
| Task preview | Ops catalog | Diagnostic only | No | No | prod dry-run | DIAGNOSTIC (eager bad) |
| Production task dry-run | Task plan | Diagnostic | No | No | task-gen | PRODUCTION (eager bad) |
| Production handoff | Prod readiness | Diagnostic | No | No | — | PRODUCTION (eager bad) |
| Task generation dry-run | Gen plan | Diagnostic | No | No | — | PRODUCTION (eager bad) |
| Order-bound readiness | Quote id for spine | Diagnostic | No | No | — | PRODUCTION (eager bad) |
| AI assist | Assist | Diagnostic | No | No | — | DIAGNOSTIC (eager bad) |
| Runtime capture | Form diagnostics | Lazy drawer | No | No | — | DIAGNOSTIC (OK lazy) |
| Product truth planner | Promotion | Lazy drawer | No | No | — | DIAGNOSTIC (OK lazy) |
| Commercial spine state | Quote lifecycle | Diagnostic | Confirm path | When mutated | dry-run | CONFIRM/PROD |

## Cost summary

- Eager GETs ≈ 17 including **6** that only feed diagnostic/production UI
- After finish autosave: up to **8–9** refetch groups including production
