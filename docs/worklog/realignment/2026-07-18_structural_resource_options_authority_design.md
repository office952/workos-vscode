# Worklog — Structural Resource Options Authority Design (+ ACP owner rules)

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO (authority) | `GO_STRUCTURAL_MATERIAL_AND_PROFILE_RESOURCE_OPTIONS_AUTHORITY_DESIGN` |
| GO (owner rules) | `GO_DEFINE_ACP_INTERNAL_FRAME_PROFILE_AND_CROSSBAR_OWNER_RULES` |
| Authority verdict | `NEW_RESOURCE_OPTION_REGISTRY_REQUIRED` |
| Owner-rules verdict | **`OWNER_DECISION_REQUIRED`** |
| HEAD | `10253ff5c52fec36c069bb6857de7401ebfc3949` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| App edits | **None** |
| Seed / migration / schema | **None** |
| Commit | **None** (awaiting owner review + interview answers) |

## Session 1 — Authority design

Delivered shared technical RO architecture (Option D), inventory audit, decision sheet skeleton, ACP contract proposal, empty crossbar worksheet.

## Session 2 — Owner rules definition

Attempted to lock ACP profiles, clearance, crossbars.

**Blocker:** Owner did not yet supply the three critical shop values:

1. profilele folosite real  
2. clearance-ul uzual  
3. regula practică pentru traverse  

Therefore:

- No profile marked `OWNER_CONFIRMED`
- Clearance 5 mm remains **GUARDED** (repo hardcode ≠ policy)
- Crossbar matrix remains **DEFERRED** → `MANUAL_OPERATOR_CONFIRMATION_REQUIRED`
- Crossbar mode **PROPOSED** as MANUAL only
- Structural boundary **PROPOSED** as `STRUCTURAL_REVIEW_REQUIRED` without invented thresholds

### Added / updated

| File | Change |
|------|--------|
| `docs/decisions/ACP_INTERNAL_FRAME_OWNER_RULES.md` | **Created** — rules pack + short interview |
| `docs/decisions/STRUCTURAL_RESOURCE_OPTIONS_OWNER_DECISION.md` | Status markers; no false APPROVED |
| `docs/templates/ACP_INTERNAL_FRAME_CROSSBAR_OWNER_WORKSHEET.md` | MANUAL / STRUCTURAL_REVIEW placeholders |
| `docs/plans/ACP_INTERNAL_FRAME_RESOURCE_OPTION_CONTRACT.md` | Step 2 + Aggregate readiness; clearance GUARDED |
| `docs/architecture/STRUCTURAL_RESOURCE_OPTIONS_AUTHORITY.md` | Blocked note for Registry V1 |
| this worklog | Updated |

## Dead pieces (report only)

- Hidden FE `enabled→frame_clearance_mm=5`
- `20x20x1.5` / `30x30x1.5` as docs/premount mentions without ACP approval
- aluminium vs aluminum spelling (convention PROPOSED: ALUMINIUM internal)
- Totem mock traverse lengths
- Premount / lightbox SKUs as false ACP catalog

## Next safe step

**Option 2 — STOP FOR REMAINING PROFILE OWNER VALUES**

Owner completes the 10-line interview in `ACP_INTERNAL_FRAME_OWNER_RULES.md`.  
Then possible: Option 3 manual-guarded registry (if ≥1 profile + materials confirmed) or Option 1 full registry.

## Roadmap checkpoint

```text
Shared technical resource authority (designed)
→ owner-approved materials/profiles/clearance/crossbars  ← BLOCKED HERE
→ registry V1
→ ACP Step 2 → PD → Aggregate → CPP → tasking → Execution
```

Stops at: owner-approved rules package **incomplete without shop values**.  
Employee Mobile remains final-final.

**Roadmap score:** 7/10  
**Alignment:** 90/100% (process correct; values missing)

## STOP
