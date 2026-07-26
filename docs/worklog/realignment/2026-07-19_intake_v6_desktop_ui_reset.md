# Worklog — Intake V6 Desktop UI Reset Audit

| Field | Value |
|-------|--------|
| Date | 2026-07-19 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Accepted functional baseline | `9f0efa0ce810ec0126ec6b3e1abe5d8d1e675602` |
| Mode | Docs-only audit — **no implementation** |
| Runtime record | FE `:3000` · `BACKEND_PORT=8003` · BE `:8003` |
| Pack | `docs/qa/intake-v6-desktop-ui-reset-2026-07-19/` |

## What was done

1. Live desktop inspection + screenshot capture (ACM fixture).  
2. Code tree mapping for Straturi / Finisaje / Iluminare / Montaj / Confirmare.  
3. Full element inventory with ownership marks (orphan, detached, false urgency, nesting noise).  
4. Warning/stress, nesting/layout, hierarchy, composition proposal, implementation boundary.  
5. Owner decision table prepared — no micro-polish implementation.

## Functional freeze respected

Support-role wiring, persistence, status semantics, guidance spine, pricing math, Montaj domain logic — not modified.

## Risks / dead pieces noted

- `IntakeV6SupportContourGeometryCard` unmounted.  
- Confirmare checklist default-collapsed.  
- Confirm handoff blocker props not rendered.  
- Dual Iluminare renderers (contract + specialized).

## Next

Owner reviews pack and GO for **one** implementation build only.
