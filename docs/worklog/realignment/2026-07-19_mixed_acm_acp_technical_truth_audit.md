# 2026-07-19 — Mixed ACM/ACP technical truth and ownership audit

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD initial | `4c682c8` |
| Scope | Docs-only audit + consolidation |
| GO | Audit / docs / Semgrep local / gh read-only — **no** product code |

## Deliverable (canonical)

`docs/architecture/MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md`

## Parallel tracks (subagents)

| Track | Agent | Focus |
|-------|-------|-------|
| Terminology ACM/ACP | [Terminology](698d3c3f-ef61-44e1-9798-7d3e5af90960) | Live ACM shell vs LIGHT-ROUTED vs Bond; plexi trap |
| Letters + șablon | [Letters/sablon](9b87a63f-08af-4824-aa8b-0e694ec22cc2) | Letter SoT, sablon_montaj, duplicate task risk |
| Frame / housing / insert | [Frame/housing](b5584a99-41b3-4de4-bb90-c0b48c4f2b29) | Frame formula, inner_hole PARTIAL, CNC/Oracal gaps |

Principal agent reconciled into one process doc without dual truths.

## Sources (mandatory + key)

- `03_PRODUCT_DEFINITION_COMPILER.md`, `05_PRODUCT_AGGREGATE_FLOW.md`, `08_EXECUTION_PLAN_FLOW.md`, `10_EXECUTION_PLAN_TASK_GRAPH.md`
- `ACP_ACM_DIBOND_TERMINOLOGY_MAP.md`, `ACP_INTERNAL_FRAME_OWNER_RULES.md`, ACP face/module docs
- Letters dossier + process graph
- Live codes: `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`, `TPL-VOLUMETRIC-LETTERS_v2`, face-treatment registry

## Tools

| Tool | Use |
|------|-----|
| `gh` | repo view + commits read-only; **zero write** |
| Semgrep 1.170.0 | `--metrics=off`; scoped rules on product_system paths — string rules returned 0 findings (engine limitation); **rg** used for occurrence evidence |
| Thunder Client | not required |

## Contradictions documented (not silently merged)

1. Frame profile SKU DEFERRED vs didactic 20×20 cutlist example → topology yes, SKU gate remains.  
2. CNC task_rules order incomplete vs owner CNC sequence → docs SoT; code gap.  
3. Șablon memoriu paper vs runtime Forex default → flagged.  
4. LIGHT-ROUTED still parallel Cost — not V6 authority.

## Files touched (docs only)

- `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` (new canonical)
- `ACP_ACM_DIBOND_TERMINOLOGY_MAP.md` (cross-link)
- `ACP_LOCAL_FACE_MODULE_OWNER_GATES.md` (pointer)
- `ACP_ACRYLIC_INSERT_LOCAL_MODULE.md` (pointer)
- `ACP_ROUTED_BACKLIT_LOCAL_MODULE.md` (pointer)
- this worklog

## Owner decisions remaining

See canonical §16 (profiles, CNC task_rules, optical RO, sablon paper/Forex, composition DAG, LIGHT-ROUTED migrate GO).

## Next step

**Superseded for scope:** complete consolidation continued in  
`2026-07-19_mixed_acm_acp_complete_process_truth.md` (finish, segmented, 220V, atelier/montaj).
