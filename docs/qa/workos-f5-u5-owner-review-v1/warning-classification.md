# Warning classification

| Warning | Track | Reprodus? | Severitate | Introdus de chain? | Clasificare | Acțiune |
|---------|-------|----------:|------------|-------------------:|-------------|---------|
| Trailing whitespace F5 report | F5 docs | Da | Low | Da | HARDEN_NOW | Fixed |
| Operator readiness 403 vs copy | U5/F3 API | Da | Med | Pre-U4B contract mismatch exposed by U5 | HARDEN_NOW | Fixed readiness permission |
| Costs panel fetch for non-management roles | U5 | Da (code path) | Med | Da | HARDEN_NOW | Gated to management |
| Incomplete prior U5 screenshot matrix | U5 | Da | Med | Da (evidence gap) | PUSH_BLOCKER→closed | Full C2 matrix captured |
| Machine cost N/A / unavailable | F5 | Da | Platform | Da (honest) | ACCEPTABLE_WARNING | Keep |
| Other-direct not_applicable | F5 | Da | Platform | Da | ACCEPTABLE_WARNING | Keep |
| Platform Profitability NOT READY | F5 | Da | Platform | N/A | ACCEPTABLE_WARNING | Keep |
| ProductSystem 404 on /execution | preexist | Da | Low | Nu | PREEXISTING_UNRELATED | Report only |
| Pricing.badges flake | FE | Da (prior) | Low | Nu | PREEXISTING_UNRELATED | No Pricing change |
| Post-job panel residual duplication | U5 | Da | Low | Partial | NEXT_BUILD | Scorecard U6 |
| Collaboration/stock compacted away | U5 | Da | Low | Da (scope) | NEXT_BUILD | Scorecard |
| Legacy reversal non-valued | Inventory | Da | Low | Nu | PREEXISTING_UNRELATED | Step 12 later |
| Canonical path workos_app_vs stale | Ops | Da | Low | N/A | DOCUMENTATION_DRIFT | Use C:\w\psiso controller |
