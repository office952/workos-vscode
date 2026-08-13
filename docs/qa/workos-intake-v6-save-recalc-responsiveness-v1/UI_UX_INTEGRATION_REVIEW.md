# UI_UX_INTEGRATION_REVIEW

## Placement decision

Operator eyes go to the sticky **Ofertă client** rail after a selector change.  
Lifecycle status is a single subtle line under the offer hero (`data-testid=intake-v6-live-offer-lifecycle`).

## Avoided

- Toast spam per selector
- Permanent “Ofertă actualizată”
- New global loading store / event bus
- Field-level save chrome on every dropdown
- Layout redesign

## Duplicate banner handling

When lifecycle label is present, the bulky `INTAKE_V6_PENDING_SAVE_BANNER` under the rail is suppressed. Footer autosave status remains as secondary technical sync text.

## Full-page check (Step 2)

| Check | Result |
|---|---|
| Hierarchy (form left / offer right) | Unchanged |
| Sticky offer rail | Intact |
| Density | One extra 10px status line when active |
| Mobile bar | Inline lifecycle next to prior “Salvare…” slot |
| Loading flicker | Ephemeral; updated flash ≤1.8s |
| Technical leakage | Romanian operator labels only |

Screenshots: `screenshots/`