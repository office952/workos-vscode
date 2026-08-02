# WorkOS U6 — Post-U5 Application Scorecard V1

**Stamp:** `PASS` (audit/read-only; no UI implementation)
**Base:** `4ec3d384`
**Runtime:** FE `:3043` BE `:8023` DB `qa-dbs/u6-scorecard.db`

## Verdict

```text
U6 APPLICATION SCORECARD PASS
Next UI wave = AppShell / role navigation / production home clarity (Wave 0 residual)
Execution Detail = do NOT redesign now (U5 accepted; no regression found)
```

## Ranked scorecard (desktop)

| Rank | Route/Page | Score | Severity | Operator impact | Owner | Recommended wave |
| ---: | ---------- | ----: | -------- | --------------- | ----- | ---------------- |
| 1 | AppShell + `/dashboard` | 48 | P1 | Role-blind nav; naming collision "Control Tower" | controller UI | **U7 shell/role nav** |
| 2 | `/shop-floor` vs `/operator` vs `/tablet` | 52 | P1 | Competing production homes | Production UI | U7 production home IA |
| 3 | `/intake` vs `/intake-v6/...` | 55 | P1 | Legacy intake vs V6 dual path | Commercial | U7 commercial handoff |
| 4 | `/inventory/pricing` | 58 | P1 | Dense admin chrome; badges flake | Pricing owner | Pricing polish GO (separate) |
| 5 | `/product-system/products` | 50 | P2 + preexisting 404 on exec preview | Lab density; PS 404 on execution | Product System | Separate PS GO |
| 6 | HR sensitive (`/employee-payments`, advances) | 45 | P0/P1 | Peer-visible nav risk | HR/admin | Role nav harden |
| 7 | `/execution/:order_id` (U5) | 72 | P2 residual | Post-job duplication residual | Execution UI | Cleanup only if scorecard insists |
| 8 | `/execution` dashboard | 65 | P2 | Entry clarity | Supervisor | After shell |
| 9 | `/quotes` `/orders` | 62 | P2 | Parametric coverage weak | Commercial | Commercial wave |
| 10 | `/utilaje` `/employees` | 60 | P2 | Registry density | Ops | Later |
| 11 | Dev/demo routes | 40 | LEGACY/DEAD | Noise in nav | Dev tooling | Hide/quarantine |
| 12 | Employee Mobile routes | n/a | FROZEN | Excluded | — | Final-final |

## Highest-risk UI page
AppShell role navigation exposing sensitive HR/finance peers and competing production homes.

## Best current UI page (among audited)
`/execution/:order_id` after U5 — clearest operational hierarchy for tested roles/states.

## Recommended next UI GO
**U7 — AppShell day-mode role navigation + single production home decision**

Alternatives:
1. Commercial handoff cleanup (Intake V6 canonical, legacy intake demotion)
2. Pricing admin density/role visibility (only with Pricing owner GO)

## Why not Execution Detail again
U5 accepted with documented limitations; C2 visual review forbids inertia redesign; residual post-job duplication is P2 cleanup, not a new wave.

## ProductSystem 404 disposition
**PREEXISTING_UNRELATED** — reproduced only on `/execution/:orderId` preview path; not repaired in U6.
