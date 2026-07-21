# ACM Boxed Support Composition — Shared Map (Decision A)

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| CP0 | `ACM_BOXED_SUPPORT_COMPOSITION_CP0_FREEZE.md` |
| Allowlist | `ACM_BOXED_SUPPORT_COMPOSITION_ALLOWLIST.md` |

## Agents

| Agent | Scope |
|-------|--------|
| A ACM Root | Seed + dossier composition sections on `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| B Applied Content XOR | `applied_content` letters\|logo contracts + validators |
| C Metal Frame | Optional `acp_internal_frame` operator selection |
| D PT/PD/Aggregate | Standalone composition graph + aggregate child mapping |
| E Qty/CPP/EIC | No double-count; separate_quote_line; anti-hourly |
| F UI/Readiness | Radio + frame checkbox; readiness honesty for logo/unpublished |
| G QA/Evidence | Tests, screenshots 1–20, final report §§1–43 |

## Identity table

| Role | Code |
|------|------|
| Root | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Letters pack | FACE / BACK / ALUMINIU / LED / FINISH |
| Logo pack root | `TPL-VOLUMETRIC-LOGO_v1` (offerability blocked) |
| Frame | `acp_internal_frame` domain |

## XOR / optional rules

1. `applied_content` ∈ {`none`, `letters`, `logo`}
2. Selecting both letters and logo → blocker `APPLIED_CONTENT_XOR_VIOLATION`
3. Logo selection → readiness warning/blocker `LOGO_BRANCH_CANDIDATE_BLOCKED` (honest)
4. Frame enabled only when operator sets `internal_frame_enabled` / nested `internal_frame.enabled`
5. No auto frame from panel size thresholds
