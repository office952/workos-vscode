# Lane F — UI observer (no page cards)

| Surface | Shared | Class |
|---------|--------|-------|
| `/shop-floor` | SourceBadge | SHARED_OK badge; DUPLICATE_PATTERN JobStatusBadge; HARDCODED_UI_CANDIDATE emerald/amber chips; WC keys as titles |
| `/execution` | MetricTile, DataTableWrapper | SHARED_OK; SHARED_PRIMITIVE_GAP no PageShell/EmptyState |
| `/execution/:id` | none at page | SHARED_PRIMITIVE_GAP; HARDCODED_UI_CANDIDATE amber/blue |
| `/execution/machine-runs` | wo-* + machineRunUi | SHARED_OK status helper; SHARED_PRIMITIVE_GAP layout |
| `/execution/ops-graph` | MetricTile, DataTableWrapper | SHARED_OK; PAGE_LOCAL_JUSTIFIED gaps |
| `/operator` | SourceBadge, StatusBadge | HARDCODED_UI_CANDIDATE policy banner; DUPLICATE_PATTERN EligibilityBadge |
| `/tablet` | SourceBadge, StatusBadge | PAGE_LOCAL_JUSTIFIED touch UI; HARDCODED_UI_CANDIDATE action colors |

No PageShell/SectionCard on these routes. Light/dark via `wo-*`; hardcoded palettes ignore tokens. Hover/focus: nav Atelier WEAK both themes; exec row WEAK; some links YES.
