# SAVE_TRIGGER_CONTROL_MATRIX_AFTER

Constants: `frontend/src/lib/intakeV6/intakeV6ReviewAutosavePolicy.ts`

| Policy | ms | Used for |
|---|---:|---|
| short | **100** | Discrete selectors (face / cant / depth / backing / lighting / PSU / mounting checkboxes) |
| long | **700** | Continuous numeric (template area; sticky latch) |
| commercial | **700** | Markup / discount / manual |
| AcmPanel draft | **500** | Unchanged |
| immediate | 0 | Unchanged |

## Classification preserved

| Class | Debounce after |
|---|---|
| DISCRETE_SELECTOR | **100 ms** coalescing |
| CONTINUOUS_NUMERIC (template area) | **700 ms** |
| CONTINUOUS_NUMERIC (commercial) | **700 ms** |
| FREE_TEXT | Explicit Save (unchanged) |
| EXPLICIT_CONFIRM | Immediate (unchanged) |

No universal debounce. No per-keystroke storm for typing fields.