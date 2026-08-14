# Lane F — UI observer (Wave 4)

| Surface | Shared | Class |
|---------|--------|-------|
| Product System V2 | `wo-*` via `productSystemSurfaces.ts` | SHARED_OK tokens; SHARED_PRIMITIVE_GAP (no PageShell/EmptyState) |
| TemplateGeneralTabPanel | local SectionCard | DUPLICATE_PATTERN |
| TemplateLibraryView chips | cyan/emerald/slate borders | HARDCODED_UI_CANDIDATE; StatusBadge `active` fallback can mislabel candidates |
| Structure workshops | wo-* + accent | PAGE_LOCAL_JUSTIFIED |
| SurfaceTruthChips | PREVIEW ONLY / NOT PRICE | PAGE_LOCAL_JUSTIFIED · honest |
| `/modules` | `presentStatusBadgeClass` | DUPLICATE_PATTERN vs StatusBadge |
| `/governance` | `governanceStatusBadgeClass` + TabHonestyBanner | DUPLICATE_PATTERN / PAGE_LOCAL_JUSTIFIED |
| Finish/Form admin panels | `bg-slate-900` | HARDCODED_UI_CANDIDATE (light-mode risk) |

Honesty: chips on V2/modules are mostly honest. Risk: TemplateLibraryView treating non-archived as `active`.
