# Implementation Boundary — Desktop UI Reset

**Baseline frozen:** `9f0efa0ce810ec0126ec6b3e1abe5d8d1e675602`  
**Mode:** Documentation / proposal only. **No implementation in this pack.**

## Must remain functionally frozen

| Area | Why |
|------|-----|
| Support-role proposal + Contur suport persistence | Accepted wiring repair |
| FinishSetup / composition confirmation persistence | Truth integrity |
| Status counts (blockers / warnings / info) semantics | Guidance spine |
| Footer primary action model (“Următorul pas”) | Operator Guidance Model |
| Pricing calculation / CostEngine / dry-run math | Commercial truth |
| Analyzer / SVG ingest / role proposal engine | Domain |
| ProductDefinition / ProductAggregate | Domain |
| Montaj IA / segmented electrical contracts | Domain — presentation may change later, logic not |
| Confirmare access honesty | Incomplete must not unlock |

## Allowed in a future implementation build (owner GO only)

- Frontend presentation / layout / hierarchy / nesting reduction
- Warning visual weight reclassification (same truth, different chrome)
- Moving technical IDs / Product System badges behind disclosure
- Local-first warning placement near owning controls
- Desktop column composition
- Collapsing inactive Montaj sections harder
- Confirmare first-paint content (not hiding primary checklist by default)

## Forbidden in any UI-reset implementation

- Backend / DB / migrations / seeds
- Analyzer behavior changes
- Pricing formula changes
- New domain fields without product decision
- Employee Mobile redesign
- Global design-system rewrite outside Intake V6 operator surfaces
- Hiding real blockers to “look calm”

## Acceptance proof required before claiming implementation PASS

1. Same functional baseline tests still pass (composition, support role, live calc).
2. Live ACM + simple letters: save/reload truth unchanged.
3. Blocker counts unchanged for equivalent workspace state.
4. Screenshots show reduced false urgency without missing blockers.
5. Owner visual acceptance of desktop hierarchy.
