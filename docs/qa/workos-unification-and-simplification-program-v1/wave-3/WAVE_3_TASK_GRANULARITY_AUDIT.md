# Wave 3 — task granularity

Lesson: commercial service ≠ execution operation ≠ task ≠ operator UI card.

| Observed relationship | Example | Class |
|-----------------------|---------|-------|
| commercial line → execution task | Wave 2 bevel: sanfren+debitare vs one CNC job | CORRECT_GROUPED (commercial) / UNKNOWN on shop-floor (20 CNC queue jobs untitled as bevel) |
| operation → shop-floor card | `CNC_ROUTING`, `LETTER_FORMING` cards | TECHNICAL_MODEL_LEAK_TO_UI |
| operation → task | V2 `task_key` 1:1 planned; not all operations become tasks | CORRECT_GROUPED (rules) |
| task → employee action | operator Start/Complete; mobile claim | OVER_FRAGMENTED (3 UIs) |
| task → MachineRun | copy + backend: MachineRun ≠ task | CORRECT (conceptual); no live run to prove UI |
| task → session | sessions derive task status | CORRECT if UI says so; operator row `assigned · Neatribuit` is FRONTEND_LABEL_COMPOSITION |
| ExecutionPlan row → operator unit | 75 277 px `/operator` list (234 tasks / 19 orders, FINITE_STATIC / UNBOUNDED) | OVER_FRAGMENTED + UNBOUNDED_LIST |
| one machine → one job | Print 1 active ORD-92400 | CORRECT_1_TO_1 this fixture |
| CNC queue 20 + LETTER_FORMING 12 | workcenter cards | OVER_AGGREGATED as “queue count” without operator next-step |

**TASK_GRANULARITY = MIXED**
