# Lane F — UI observer (no page cards)

Compared to `frontend/src/components/workos/design-system`.

| Surface | Shared used | Classification |
|---------|-------------|----------------|
| `/intake` | PageShell, AlertBanner, SourceBadge, StatusBadge | SHARED_OK badges; PAGE_LOCAL_JUSTIFIED pipeline cards; SHARED_PRIMITIVE_GAP list (no DataTableWrapper); DUPLICATE_PATTERN vs Orders master-detail |
| Intake V6 | AlertBanner only | HARDCODED_UI_CANDIDATE — parallel `v6` token layer; HeroMetricTile / LayerStatusBadge local; commercial rail page-local money |
| `/orders` | StatusBadge, SourceBadge | SHARED_PRIMITIVE_GAP list; PAGE_LOCAL_JUSTIFIED “no re-price” honesty; DUPLICATE_PATTERN flux strip |
| `/clients` | none | HARDCODED_UI_CANDIDATE entire page; fiscal badge outside DS |
| Client workspace | none | DUPLICATE_PATTERN tabs vs spine lists; Overview EN label |

Light/dark: both themes captured on admin for all primary routes. Light sidebar still cooler than canvas (Wave 1 systemic). V6 Configurare commercial rail remains readable in both. Money emphasis: EUR on V6/quotes vs RON on orders/clients — not a theme issue, a **truth** issue (see contradictions).

Hover/focus: sampled on nav, row, search, primary CTA, secondary, V6 tab, disabled handoff — light+dark. CTA/tab/secondary focus WEAK_OR_NONE both themes. Disabled confirm CTA photographed (gray “Continuă către ofertă”).
