# NETWORK_WRITE_GET_TRACE

## Ordinary discrete single selection

Observed after face change on QA clone:

| Kind | Count | Endpoints |
|---|---:|---|
| PUT | 1 | `finish-setup` |
| Offer-critical GET | 4 | `material-breakdown`, `pricing-input-preview`, `priced-quote-dry-run`, `quote-handoff-preview` |
| Other GET | logical-list / AI assist / health (existing) | not production/task |
| Production / task GET | **0** | with diagnostic drawer closed |

GET-diet invariant preserved.

## Rapid burst

One operator intent burst → **one** PUT (coalesced). No uncontrolled write storm.