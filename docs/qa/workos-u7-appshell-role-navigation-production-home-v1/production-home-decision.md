# Canonical production-home decision

## Decision

```text
CANONICAL_PRODUCTION_HOME = /shop-floor
Label = Atelier
```

## Why

- Aligns with `executionFlowUi` stage “Atelier” path (`/shop-floor`)
- Answers ready/blocked/monitor without inventing operational_tasks
- Does not depend on Employee Mobile
- Does not claim planned_tasks are operational_tasks
- Operator/Tablet remain action surfaces (compat), not peer homes
- Control producție remains management aggregate under Management

## Role homes

| Role | Home |
|------|------|
| operator | `/shop-floor` |
| manager | `/shop-floor` |
| admin | `/dashboard` (keeps management landing; Atelier still primary in Producție) |
| sales | `/quotes` |
| viewer | `/dashboard` |

## Honesty

Live Shop Floor data may be unavailable without backend contract — page states this; U7 does not invent machine/job truth.
