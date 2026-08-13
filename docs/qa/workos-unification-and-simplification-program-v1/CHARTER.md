# WORKOS Unification and Simplification Program — Charter

| Field | Value |
|-------|--------|
| Program | `WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM` |
| Date | 2026-08-13 |
| Authorization | **MEGA-AUDIT + CHARTER + DOCS/EVIDENCE ONLY** |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` |
| Implementation | NO |
| Cleanup | NO |
| Unfreeze | NO |
| Owner DB mutations | 0 |
| Agents assign FINAL | NO |
| After Wave 1 | **STOP** · `NEXT_TASK = NOT_AUTHORIZED` |

## 1. What this program is

A bounded, evidence-first program to make WorkOS one coherent operator product: page-by-page interactive audit, light and dark, user journeys, shared primitives instead of page-local chrome, architecture/ownership honesty, then later Owner-GO cleaning and simplification waves.

This charter does **not** unfreeze the laboratory reference. It does **not** authorize code changes.

## 2. What this program is not

- Not a screenshot-only gallery
- Not a route-file inventory counted as “audited”
- Not a redesign, token rewrite, or legacy deletion campaign
- Not Workflow-ADV product implementation
- Not Product System / CostEngine / offer / Execution expansion

A page is **not** audited until its full interactive surface has been traversed and the four mandatory manifests are reconciled.

## 3. Binding reuse (do not invent parallel standards)

| Doc | Role |
|-----|------|
| [`docs/architecture/WORKOS_PAGE_COMPLETION_FOUNDATION.md`](../../architecture/WORKOS_PAGE_COMPLETION_FOUNDATION.md) | DoD A–I, page statuses, Documentation Impact Gate |
| [`docs/architecture/WORKOS_UI_TERMINOLOGY_REGISTRY.md`](../../architecture/WORKOS_UI_TERMINOLOGY_REGISTRY.md) | Romanian-first labels |
| [`docs/architecture/realignment/19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md`](../../architecture/realignment/19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md) | Classify, do not delete |
| [`docs/architecture/realignment/17_UI_NAVIGATION_AND_LABELING_POLICY.md`](../../architecture/realignment/17_UI_NAVIGATION_AND_LABELING_POLICY.md) | Nav honesty |
| [`docs/freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md`](../../freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md) | Allowed change classes |
| U1/U2 baseline | Seed only — stale first-viewport, mostly light |
| U7 role homes | Canonical homes: admin `/dashboard`, sales `/quotes`, operator/manager `/shop-floor` |

Disposition tags (reuse): `KEEP` · `RENAME` · `MOVE` · `MERGE` · `HIDE_BY_ROLE` · `ADMIN_ONLY` · `LEGACY_LABEL` · `DEFER` · `REMOVE_CANDIDATE_ONLY`.

Recurring operator lesson (back bevel GO): **serviciu comercial separat ≠ task de execuție separat**. Flag every place the UI exposes internal 1:1 structures as the operator story.

## 4. Wave gates

| Wave | Scope | Status |
|------|--------|--------|
| **0** | This charter, protocol, route inventory, primitive catalog, four manifest schemas | Authorized |
| **1** | AppShell + three role homes + follow every visible nav edge once; fill four manifests | Authorized |
| **2+ orch** | Multi-agent orchestration design (`orchestration/`) | Authorized — design only |
| **2+** | Bounded page audit per later Owner GO (see `orchestration/WAVE_2_SCOPE_RECOMMENDATION.md`) | Not authorized |
| **J** | Cross-page journeys | Not authorized |
| **P** | Primitive-gap synthesis | Not authorized |
| **A** | Architecture / ownership vs realignment 00–23 | Not authorized |
| **L** | Dead / legacy / overengineering classification | Not authorized |
| **C / S** | Cleaning E2E + simplification | Later Owner GO; usually requires unfreeze |

## 5. Mandatory evidence (PNG folder is insufficient)

1. `SCREENSHOT_COVERAGE_MANIFEST.md`
2. `PAGE_INTERACTION_INVENTORY.md`
3. `NAVIGATION_AND_LINK_GRAPH.md`
4. `LIGHT_DARK_VISUAL_RUBRIC.md`

See [`TRAVERSAL_PROTOCOL.md`](./TRAVERSAL_PROTOCOL.md). Full vertical scroll exhaustion is mandatory (`FULL_VERTICAL_SCROLL`, `BOTTOM_REACHED`, `SCROLL_SEGMENT_COUNT`, `NESTED_SCROLL_CONTAINERS`). First-viewport-only is FAIL.

## 6. Operating rules

- Owner uses browser + chat only. Agent starts or reuses detached `:3000` + `:8000`. Never kill ports. Never run foreground `dev.ps1`.
- Prefer existing fixtures / dry-run. Do not mutate Owner `dev.db`.
- If a state needs mutation, mark `STATE_NOT_REACHED` and stop.
- Local commit of evidence only if Owner asks. Push / PR / merge / deploy = no.

## 7. Non-goals (explicit)

No Product System feature work · no CostEngine / pricing / offer / Execution changes · no Workflow-ADV product code · no deletion of `/operator`, `/tablet`, or V4 residue · no global theme rewrite even if day-mode is incomplete · no claiming the 2026-08-02 baseline “done”.
