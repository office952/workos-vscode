# Wave 4 gap closure — premount scope

Template: `TPL-METAL-PREMOUNT-STRUCTURE_v1`

| Lens | Evidence |
|------|----------|
| BACKEND_OFFERABLE | **YES** — `template_usage_mode_policy.py` `root_offerable=True`, `linked_child_allowed=True`; in `ROOT_OFFERABLE_TEMPLATE_CODES` |
| FRONTEND_ACTIVE_SCOPE | **OMITTED** — `activeTemplateScope.ts` `OWNER_VALID_ACTIVE_TEMPLATE_CODES` = Letters v2 + ACM boxed only. `BACKEND_ROOT_OFFERABLE_TEMPLATE_CODES_PARITY` also lists only those two (stale “mirror”). |
| ROUTE_VISIBILITY | Hidden from operator catalog (`isOperatorVisibleCatalogProduct` uses `isOwnerValidActiveTemplate`). Advanced/internal / Template Library can still name it. |
| INTAKE_REACHABILITY | Linked mounting option, **not** a Work Intake root picker. |
| QUOTE_REACHABILITY | Excluded as standalone root (`filterActiveTemplatesForQuote`). Reachable only as linked child via Letters mounting. |
| EXECUTION_REACHABILITY | Optional linked module in volumetric mini-module / aggregate path — not a standalone sold root in the Wave 2/3 fixture. |

**PREMOUNT_SCOPE_RELATION = TRUE_SCOPE_DRIFT**

The FE comment claims to mirror backend `ROOT_OFFERABLE_TEMPLATE_CODES`, but the FE list and the FE “parity” constant both omit premount while backend policy includes it. Catalog hide and quote-root exclude are **consequences** of that FE list (`INTENTIONAL_UI_FILTER` downstream), not a separate product decision documented as “premount is not offerable.”

No activation in this GO. W4-C4 remains **ACTIVE**.
