# Role matrix (audit)

| Role | Surfaces observed | Fail-closed notes |
|------|-------------------|-------------------|
| Admin (dev bypass) | Full nav; all audited routes load | BE permissions still gate mutations |
| Operator | Not re-impersonated in U6 capture (C2 proved execution readiness/close split) | Mobile excluded |
| Commercial | Quotes/orders/clients visible in shell | Must not see internal cost aggregates (U5 gate) |
| Unknown | Auth routes only | Shell redirects unknown to dashboard |

U6 did not implement role-nav fixes — recommendation only.
