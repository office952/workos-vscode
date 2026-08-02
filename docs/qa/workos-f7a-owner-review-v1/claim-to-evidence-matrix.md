# F7A Owner Review — Claim → Evidence Matrix

Independent verification at `6c3af83d`. Executor report is not accepted as sole proof.

| Afirmație F7A | Dovadă cod | Dovadă test | Dovadă runtime | Verdict |
|---------------|------------|-------------|----------------|---------|
| `task_rules` is the only driver | Aggregate → freeze → `collect_effective_task_rules` → EP preview | F7A + preview suites | Preview builds from frozen Aggregate task_rules | **PASS** (synth fill for uncovered ops = residual channel) |
| Alias mapping single owner | `_MODULE_ALIAS_TO_PARENT` only in `product_process_aggregate_bridge.py` | collapse unit tests | n/a | **PASS** |
| RETURN aliases not tasks | collapse + EP identity skip | F7A + golden DAG | preview ops exclude RETURN_PROFILE_* | **PASS** |
| PAINTING alias not task | same | same | painting once | **PASS** |
| WC upstream and frozen | Preview reads Aggregate ops only | F7A asserts WC projection | stamped ops project | **PARTIALLY_PROVEN** (`WC_CNC` ≠ registry `WC_CNC_ROUTING`) |
| Minutes remain null | preview null path | F7A asserts | probe all null + warning | **PASS** |
| Linear fallback removed (EP V2) | `_build_dependencies` warns, no chain | `test_dag_no_universal_linear_fallback…` | n/a | **PASS** |
| Fixture DAG valid | process deps on rules | F7A + Lead probe | bond←face+side; unresolved warn **absent** | **PASS** |
| Premount BOM-only default | absent from fixture task_rules | `test_dec002…` | not in planned ops | **PARTIALLY_PROVEN** (no hard synth ban) |
| SVG non-operational | `NON_OPERATIONAL_PROCESS_CODES` | `test_dec001…` | absent from planned | **PASS** |
| Audit GET no writes | audit service guards | F7A counts + spy | n/a (service-level) | **PASS** |
| POST gate 422 | `dec009_materialize_gate` | F7A `@enforce_dec009_gate` | n/a (no live POST) | **PASS** |
| Materialize service call count 0 | spy on materialize service | F7A | n/a | **PASS** |
| Protected baseline unchanged | n/a | n/a | sqlite `973019` hash/total | **PASS** |
| Commercial total unaltered | F7A touch set excludes commercial | fixture total assert | baseline 847.5 unchanged | **PASS** |
| Dashboard → Intake V6 entry | Dashboard→`/intake`; V6 gated `demos` | n/a | browser FAIL | **FAIL** (UI track) |
