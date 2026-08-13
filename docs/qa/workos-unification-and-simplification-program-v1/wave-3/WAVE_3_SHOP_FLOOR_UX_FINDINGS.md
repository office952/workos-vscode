# Wave 3 — Atelier / shop-floor UX

What operator sees first: FLUX + “Următorul pas: Acționează pe task” + machine grid. Primary action is **not on this page** — banner sends to COMPAT `/operator` / `/tablet`.

| Question | Answer |
|----------|--------|
| Next work obvious? | PARTIAL — queues 20/12 visible; live job is a different order |
| Priorities? | Weak — idle vs queue count |
| Statuses human? | Mixed — Idle/QUEUE vs `CNC_ROUTING` |
| Sequence? | No sequence; workcenter grid |
| Machine deps? | Card occupancy only |
| Assignment? | Empty operator on Print job |
| Ready vs blocked? | Copy claims this; blocked board click did not change story much |
| Planned vs actual? | Not on first fold |
| IDs? | ORD-92400; WC enum keys |
| Graph detail? | No (good) |
| Manager leak? | FLUX includes Control producție |

Block classes: machine grid OPERATOR_CRITICAL; FLUX/next-step MANAGER; WC keys TECHNICAL; Live tick DIAGNOSTIC.

**SHOP_FLOOR_OPERATOR_STORY = TECHNICAL / PARTIAL**
