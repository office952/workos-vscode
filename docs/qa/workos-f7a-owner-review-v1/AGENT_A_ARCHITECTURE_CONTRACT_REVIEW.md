# Agent A — Architecture & Contract Review (consolidated)

Independent read-only review at `6c3af83d`. Full detail preserved from Agent A run.

## Verdict

```text
ARCHITECTURE / CONTRACT = PASS WITH DOCUMENTED GAPS
DEC-009 FROM ARCHITECTURE = REMAIN A
F7B = NOT AUTHORIZED
```

## Claim verdicts (summary)

| Claim | Verdict |
|-------|---------|
| Single alias mapping owner (`product_process_aggregate_bridge.py`) | PASS |
| No duplicate compiler / all-ops fallback on F7A path | PARTIALLY_PROVEN (composition-graph synthesis remains) |
| RETURN_PROFILE_* / PAINTING excluded when parents present | PASS |
| Parent canonical ops preserved | PASS |
| WC upstream → freeze → plan; not invented in EP | PARTIALLY_PROVEN (`WC_CNC` vs registry `WC_CNC_ROUTING`) |
| Linear DAG fallback removed from EP V2; legacy isolated | PASS |
| Premount BOM-only; SVG non-operational | PARTIALLY_PROVEN (no hard premount ban on synth path) |
| Commercial / Pricing / HR untouched | PASS |

## Blocking / pre-B gaps

1. Premount not hard-excluded from composition-graph candidate synthesis.
2. Fixture WC `WC_CNC` is not the ORR seed code `WC_CNC_ROUTING` (transitional parity exists elsewhere; registry-honest fidelity incomplete).
3. Architecture docs 08/21/10 still lag F7A (linear DAG / pending DEC language).
4. Live ORR→freeze chain for real volumetric products not re-proven beyond stamped Aggregate fixture.

## Doc contradictions (report only — no sync in this review)

- `08_EXECUTION_PLAN_FLOW.md` still describes linear `depends_on` and pending DEC-003–005/009.
- `21_WORKOS_IMPLEMENTATION_ROUTE.md` still lists duplicate lateral ops / WC null.
- `10_EXECUTION_PLAN_TASK_GRAPH.md` wording that dossier task_rules are “not driver” conflicts with current Aggregate→EP spine.
