# Closed-job mutation guards

Preferred Owner behavior implemented:

```text
closed execution → mutation rejected (409 execution_closed_mutation_blocked)
→ authorized reopen with reason
→ mutation allowed
→ final margin unavailable while reopened
→ reclose restores final margin when categories complete
```

Guard module: `backend/services/closed_job_mutation_guard.py`
Wired into canonical material writers + deduction + order-linked reversal.
Silent post-close margin mutation is blocked at write path, not only UI.
