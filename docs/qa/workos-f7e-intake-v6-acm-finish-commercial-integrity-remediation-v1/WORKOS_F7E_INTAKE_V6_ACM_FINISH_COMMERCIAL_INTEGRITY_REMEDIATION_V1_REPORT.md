# WORKOS F7E — Intake V6 / ACM Finish Commercial Integrity Remediation

## Verdict

```text
F7E = PASS_WITH_OWNER_RULE_BLOCKERS
PROVEN-RULE P0/P1 = CLOSED
MISSING-RULE FINISHES = FAIL-CLOSED
SILENT ZERO DELTA = ELIMINATED (for proven Oracal/RAL/none paths)
OWNER COMMERCIAL DECISIONS = ACM shell finishes, Oracal color-tier, print/laminate face rates
COMMERCIAL INTEGRITY = UNBLOCKED for proven finish branches; BLOCKED for Owner-rule-missing branches
SCHEDULING ROADMAP = HOLD
PUSH = NOT EXECUTED
MATERIALIZATION GATE = CLOSED
PROTECTED BASELINES = PASS
```

## Exact F7D P0/P1 register (closed)

| ID | Severity | Status after F7E |
|----|----------|------------------|
| AGENT-B-F001 | P0 | **CLOSED** — finish-sensitive CPP (Oracal face/cant, RAL) |
| AGENT-B-F002 | P0 | **CLOSED** — CPP uses registry commercial rules, not EIC totals |
| F1/B-F005 | P0 | **CLOSED** — single ACM inclusion state (UI) |
| A-F4 | P0 | **CLOSED** for status language; residual Step 3 ACM EUR line-list completeness = follow-up |
| A-F2 | P1 | **CLOSED** — optional ACM include checkbox |
| A-F3 | P1 | **DEFERRED** (out of Agent C file ownership) |
| AGENT-B-F003 | P1 | **CLOSED** in code (template-aware geometry); ACM suite fixture env ERROR locally |
| AGENT-B-F004 | P1 | **CLOSED** — Literal finish tokens |

## Live commercial proof (API)

| Scenario | Result |
|----------|--------|
| none | 490.0 — no flat 35 finish line |
| Oracal 8500 vs none | **+112.5** RON |
| Oracal 8500 vs 641 | **+33.75** RON |
| Stock cant colors | zero-delta 490.0 |
| RAL cant | +100 floor |
| Oracal wrap cant | +47.2 dedicated lines |
| print_laminate | `COMMERCIAL_RULE_MISSING` blocked |
| paper→Forex | +10 preserved |

Evidence: `runtime-proof.json`, `captures/`, screenshots.

## Architecture

```text
Normalized finish selection
  ├──→ EIC (internal, unchanged consumer)
  └──→ CPP (commercial rules + registry rates; no EIC import)
```

## Owner decisions still required

- ACM mass color / mirror / shell finishes commercial rates
- Oracal color-tier (same series, different code)
- print/laminate face commercial activation (fail-closed today)
- Confirm face-Oracal legacy CPP wiring vs Product System FACE workshop tag (Lead used F7E GO + proven MAT-ORACAL-* rates)

## Tests (Lead)

- Backend targeted: **85 passed** (CPP preview + vocab + F7C readiness + DEC-009 gate)
- Frontend targeted Vitest: **59 passed** (6 files)
- ACM standalone suite: fixture `db_manager` setup ERRORs in this environment (pre-existing harness issue)

## Protected

880811 / 973019 snapshot prefixes and totals unchanged. Gate `pilot_gate_open=false`.
