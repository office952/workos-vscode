# ACP Illumination & Electrical Ownership

**Chosen mode:** `SHELL_COMMON_WITH_ZONE_INTENTS`

## Model

```text
Face treatment / local module
  → declares illumination_intent (enabled, lighting_mode, gate statuses)

ACP electrical configuration (finish.acp_electrical_configuration)
  → composes zone_intents from active modules
  → owns LED / PSU / wiring / service / test statuses (gated)
  → reuses service_corner from shell when present
```

## Explicit non-goals

- No duplicate PSU per zone
- No LED quantity invent in UI
- No electrical authority in SVG Analyzer
- Letters illuminated volumes ≠ ACP cavity path
- Legacy `TPL-ACP-LIGHT-ROUTED` remains `PARALLEL_LEGACY_COST_PATH`

## Resource authority

Optical / electrical Resource Options catalogs: **MISSING**.  
Do not reuse Structural RO for plexiglas/LED. Owner gates retained until catalogs exist.
