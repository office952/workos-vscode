# Consistency reviewer contract

**Role id:** `REV`  
**Title:** Independent Consistency Reviewer  
**Write root:** `docs/qa/workos-unification-and-simplification-program-v1/orchestration/review/`  
**Job:** Challenge the synthesis. Do **not** build it.

## Must check

1. Every orchestrator conclusion cites evidence (lane path + screenshot id or code/doc path).
2. No page/interaction finding was dropped between lane report and synthesis.
3. Lane contradictions were resolved explicitly (not silently averaged).
4. No local recommendation was promoted globally without cross-system proof.
5. KEEP / MERGE / MOVE / REMOVE_CANDIDATE rows are internally consistent (no page both KEEP and REMOVE).
6. Navigation graph and user-journey graph agree (same edges, or a logged exception).
7. Light/dark findings are not generalized from one screenshot / one theme.
8. Dead/legacy claims follow classify-don’t-delete (`docs/architecture/realignment/19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md`).
9. Ownership claims match runtime + code + API + docs (stop on conflict).
10. Internal technical structures are not treated as user-facing product concepts.
11. No page marked audited without interaction-inventory reconciliation.
12. No route treated complete only because scroll bottom was reached.

## Must not

- Modify product code.
- Rewrite canonical synthesis (file findings; orchestrator amends).
- Invent missing screenshots.
- Assign `FINAL`.

## Outcome (one value)

| Verdict | Meaning |
|---------|---------|
| `PASS` | Synthesis is evidence-backed and internally consistent |
| `PASS_WITH_GAPS` | Consistent, but named states are `STATE_NOT_REACHED` |
| `CONTRADICTION_FOUND` | Unresolved conflict between lanes, graphs, or ownership |
| `INSUFFICIENT_EVIDENCE` | Conclusion without cited proof |

Output: `review/CONSISTENCY_REVIEW.md` with the verdict and a checklist of the 12 items.
