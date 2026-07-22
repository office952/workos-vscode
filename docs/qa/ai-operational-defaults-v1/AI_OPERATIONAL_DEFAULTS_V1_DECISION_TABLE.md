# Initial AI Decision Table (pre-implementation)

Currency aligned with catalog (EUR). Conservative mid-market workshop defaults. Configurable.

| Domain | decision_id | Formula | Unit | Initial | Min | Conf. | Rationale | Templates |
|--------|-------------|---------|------|--------:|----:|-------|-----------|-----------|
| Packaging | `AI_PACK_PRODUCT_BAND` | `max(min, band(face_area_m2))` bands S/M/L + fragile add-on | EUR/produs | 25 / 45 / 80 (+25 fragile) | 20 | MEDIUM | Size-category packaging; not time; not flat for all | VL, Logo, ACM shell, Volum Aluminiu |
| Electrical | `AI_ELEC_PRODUCT_PSU` | `max(min, min + per_psu×psu_count)` | EUR/produs | min 30; +15/PSU | 30 | MEDIUM | Setup + PSU complexity; no minutes | VL, Logo (illuminated) |
| LED install | `AI_LED_PER_MODULE` | `module_count × rate` | EUR/module | 0.35 | 0.20 | MEDIUM | Module-count driven; not `led_assembly_time` | VL, Logo |
| ACM panel labor | `AI_ACM_PANEL_LABOR_M2` | `panel_area_m2 × rate` | EUR/mp | 12 | 8 | LOW | FOLD/MOUNT ops without formula; shell only | ACM |
| Prepress | — | — | — | — | — | — | Gate ≠ labor qty → **real skip / OPERATION_ONLY** (no AI invent) | VL |

## Blocker demotion plan

| Blocker | Current | New | Reason |
|---------|---------|-----|--------|
| AMBALARE_COMMERCIAL_RULE | blocks commercial line | AI_DEFAULT_ACTIVE | packaging AI covers |
| PACKAGING MISSING_OWNER_FORMULA | owner required | AI_DEFAULT_ACTIVE | same |
| ELECTRICAL OPERATION_ONLY | unresolved | AI_DEFAULT_ACTIVE | elec AI |
| LED throughput unbound | warning only | INFORMATIONAL | qty-key + AI rate/module |
| ACM treatment commercial | blocked | **BLOCKER retained** | structural/owner rates |
| PREPRESS OPERATION_ONLY | unresolved | WARNING / OPERATION_ONLY | no safe qty → no AI invent |

## Precedence reminder

Measured / owner / catalog always beat these AI values.
