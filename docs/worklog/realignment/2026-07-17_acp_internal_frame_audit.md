# Worklog — ACP Internal Frame Existing Contract Audit

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Owner GO | `GO_AUDIT_ACP_INTERNAL_FRAME_EXISTING_CONTRACT_AND_RUNTIME_ONLY` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD at audit | `525ab979b1ea5e42eea39659d3dc5b97cde1a382` |
| Verdict | `INTERNAL_FRAME_EXISTS_AS_PARTIAL_CONFIGURATION` |
| App edits | **None** |
| Commit | **None** (awaiting owner review) |

## What was done

1. Baseline HEAD/branch/runtime (FE `:3000`, BE `:8001`).
2. Global search for internal frame / reinforcement / clearance / metal-frame lookalikes.
3. Traced Step 1 → mounting → PD → Aggregate → lifecycle → CPP boundary.
4. Distinguished ACP internal frame vs Metal Premount / letter `metal_frame` / mounting-bar `20x20`.
5. Runtime proof on workspace `f07058e2-3b40-4935-b55a-6a10b457241b`: enable flag → clearance 5 → restore baseline.
6. Wrote audit + source map + recommendation docs.

## Deliverables

- `docs/audits/2026-07-17_acp_internal_frame_existing_contract_audit.md`
- `docs/architecture/ACP_INTERNAL_FRAME_SOURCE_MAP.md`
- `docs/plans/2026-07-17_acp_internal_frame_modeling_recommendation.md`
- this worklog

## Key findings (short)

- Exists as **boolean + hardcoded clearance 5 mm**.
- Not a complete technical component (no steel/Al, profile, processes, Aggregate lines).
- Step 1 checkbox is a **marker**; Step 2 shows clearance, not frame BOM.
- PD projects boolean only; Aggregate ignores frame.
- Recommendation: **Option 2 local config completion**; material as Resource Option.

## Roadmap awareness checkpoint

| Item | Note |
|------|------|
| Active path isolation | Unchanged; audit only |
| ACP persistence / Step 2 dims | Prior GO complete; frame still partial |
| Lifecycle CI prep | HEAD `525ab97`; frame not a CI subject |
| Metal Premount baseline blockers | Separate track — do not conflate with ACP frame |
| Next product modeling | Await owner GO on Option 2 |

**Roadmap score:** 7/10 (direction clear; material/profile catalog still owner-gated)

**Alignment with established direction:** 85/100% (local ACP nested config matches composition authority; not inventing parallel template)

## Owner correction (2026-07-18)

- Rejected audit implication that cadru interior vs premontaj = XOR.
- Product Truth default: **independent**, optionally activatable, no mixed authority.
- Declared binding guards XOR mounting-support templates only; not nested frame vs premount.

## Next safe step

Option 2 — GO ACP LOCAL FRAME CONFIGURATION COMPLETION (blocked until Resource Options + profile catalog owner GO).

## STOP
