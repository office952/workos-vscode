# Worklog — ACP full system audit + Blueprint docs finalize

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_FINALIZE_BLUEPRINT_AUDIT_AND_AUDIT_ACP_COMPOSABLE_FACE_SYSTEM` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `f741006` |
| HEAD after Blueprint commit | `e7082c2` |
| Mode | Blueprint docs commit + ACP audit docs (uncommitted) |

## Blueprint finalize

Commit: `e7082c2` — `docs(product-system): record Blueprint historical UI audit`  
Exact-path staging of 5 accepted Blueprint audit files. Unrelated WIP untouched.

## ACP audit verdict

`ACP_SHELL_LIVE_MIXED_FACE_MISSING_AUTHORITY_FORK_BLOCKS_COMPOSITION`

First failing boundary: SVG component-binding contract + FinishSetup (no face-treatment roles / zones).

Recommendation: **Option 4 — FIX AUTHORITY/PERSISTENCE CONFLICT FIRST**  
Follow-on preferred: Option 2 (ACP base + local face modules) + Dossier-inspired PS UI patterns.

## Deliverables (ACP — not committed)

- `docs/audits/2026-07-18_acp_acm_dibond_alucobond_full_system_audit.md`
- `docs/architecture/ACP_ACM_DIBOND_TERMINOLOGY_MAP.md`
- `docs/architecture/ACP_FACE_COMPOSITION_SOURCE_MAP.md`
- `docs/audits/2026-07-18_acp_face_treatments_composability_audit.md`
- `docs/plans/ACP_FACE_TREATMENTS_MODEL_RECOMMENDATION.md`
- `docs/worklog/realignment/2026-07-18_acp_full_system_audit.md` (this file)

## App edits

None for ACP audit.

## Runtime

FE `:3000` up · BE `:8001` STALE (persistence guarded) · mixed-face structural fail independent of BE refresh.

## Roadmap checkpoint

```text
Product System authority
→ historical UI audit accepted (e7082c2)
→ ACP truth discovery (this audit)
→ composable face treatments  ← STOP HERE (recommend)
→ Dossier-inspired administration UI
→ ProductDefinition → Aggregate → CPP → Snapshot → tasking → Execution
```

Employee Mobile remains final-final. No UI/templates/pricing/tasking implemented in this GO.

## Next

**STOP FOR OWNER REVIEW** — recommended next GO token: **FIX ACP AUTHORITY CONFLICT FIRST**  
(Do not auto-start Option 1/2/3 implementation.)
