# GROUPED_RETURN_CANT_TRACE

## Matrix / handoff

`letter_group_finish_matrix` preserves per-group `return_depth_mm` + `return_finish_type` (adapter).

## CPP after repair

| Scenario | Result |
|---|---|
| Oracal g30 (5 ml @ 30) + g100 (7.5 ml @ 100) | material wrap area **0.90 m²** → 4.5 EUR @ 5/m²; labor **12.5 EUR** (5+7.5 ml @ 1 EUR/ml) |
| RAL g30 (5 ml @ 30) + g100 (7.5 ml @ 100) | material **40 EUR**; labor **12.5 EUR** |

Job-level dominant depth no longer erases group economics when groups carry complete perimeter+depth.  
Oracal labor never uses total wrap area or averaged width.
