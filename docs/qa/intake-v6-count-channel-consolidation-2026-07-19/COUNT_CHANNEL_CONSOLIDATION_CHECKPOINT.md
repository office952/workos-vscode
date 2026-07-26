# Count Channel Consolidation — Design Checkpoint

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `46ead84`  
**Mode:** Presentation only — **do not code before owner-agent acceptance of this checkpoint** (this build proceeds after writing it).

## Pre-flight (inventory)

| Item | Value |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `46ead84` |
| Foreign WIP | Present — untouched |
| FE / BE | `:3001` / `:8003` 200 |
| Guidance model | `buildIntakeV6OperatorGuidanceModel` |
| Sticky count | `buildOperatorBlockerBannerDisplay` → `blockerCount` / `warningCount` / `summaryTitle` (“N elemente”) |
| Footer count | `guidance.countsLabel` (“N blocante · M avertizări”) — often only final blockers |
| Drawer count | `buildIntakeV6FooterIssuesDisplay.totalCount` (“Probleme și avertizări — N”) — header details + warnings + primary action |
| Final blockers | `buildFinalConfirmationBlockers` (composition / segmented / electrical) |
| Vocabulary | `operatorStatusSemanticRo` — Blocant / Avertizare / … |

---

## 1. Current count sources

| Source | What it counts | Severity words |
|--------|----------------|----------------|
| A. Final confirmation blockers | Composition, segmented validation, electrical draft | blocker / warning |
| B. Sticky banner inventory | A + handoff surfacing + runtime/planner codes + missing-price lines | blocker / warning → “N elemente · M avertismente” |
| C. Guidance model | A (or max with unused overlay props); synthesizes +1 if nextAction | “N blocante · M avertizări” |
| D. Footer drawer | Primary next-action + header status details + review/secondary warnings + status actions | “Probleme — N” (flat total) |

## 2. Duplicate calculations

- Final blockers built in ReviewStep **and** again inside guidance model.
- Sticky and guidance both derive counts, with **different inputs** → sticky “3 elemente” vs footer “1 blocant”.
- Drawer total includes primary action + informational header rows → “7 probleme” while guidance shows “1 blocant · 1 avertizare”.

## 3. Current UI consumers

| Consumer | File | Role today |
|----------|------|------------|
| Sticky | `IntakeV6ReviewOperatorBlockerBanner` | Attention summary + expand details |
| Footer spine | `IntakeV6OperatorWorkspaceFooter` | Status · progress · counts · Următorul pas |
| Drawer | same footer | Flat “Probleme — N” + mixed groups |
| Confirm | no sticky | Footer/drawer only |

## 4. Proposed single count model

Extend **Operator Guidance Model** (no parallel engine):

```text
attentionIssues[]   // presentation inventory (deduped)
  severity: blocker | warning | information
  message, action?, focusTarget?, tabId?

blockers[] / warnings[] / information[]  // views of attentionIssues
blockerCount / warningCount / informationCount
countsLabel          // sticky + spine compact
stickySummaryTitle   // sticky headline
drawerToggleLabel    // drawer chrome
nextAction           // footer only (unchanged role)
```

**Authority of inventory on Configurare:** the sticky issue list from `buildOperatorBlockerBannerDisplay` (already merges final blockers + surfacing + technical). Guidance **presents** that list; it does not invent new domain blockers.

**On Confirmare / Straturi:** inventory = final blockers (review/confirm) + synthetic blocker from nextAction when needed + drawer information rows that are not duplicate of nextAction.

## 5. Blocker / warning / info separation

| Bucket | Meaning | UI |
|--------|---------|-----|
| Blocant | Blocks Continuă / final confirm | Sticky + drawer “Blocante” |
| Avertizare | Needs attention, not the Continuă gate alone | Sticky + drawer “Avertizări” |
| Informativ | Context / technical / non-gate | Drawer “Informații” only (not sticky headline) |

Use existing vocabulary: Blocant · Avertizare · Informativ. No Critical/Urgent/Danger.

## 6. Footer behavior

Answers: **What do I do now?**

- Keep: status · progress · **Următorul pas** (nextAction).
- Counts in spine stay compact (`1 blocant · 2 avertizări`) from the **same** model — not a counter dashboard.
- Do **not** put primary next-action as the first drawer inventory item (avoid duplicate).

## 7. Sticky behavior

Answers: **How much attention is needed?**

```text
Configurarea necesită atenție
1 blocant · 2 avertizări
Următorul pas este în footer. Deschide lista pentru detalii.
```

- `summaryTitle` built from guidance counts (same numbers as footer spine).
- No full next-action paragraph (already suppressed).

## 8. Drawer behavior

Answers: **What are all issues?**

```text
Blocante — 1
Avertizări — 2
Informații — 4
```

- Groups from guidance inventory (+ optional technical/info from header that are not already in sticky issues).
- Navigation / focus targets preserved from sticky issues.
- Toggle label uses severity breakdown, not opaque “Probleme — 7”.

## 9. Example before / after

**Before**

```text
Sticky:  3 elemente · 1 avertisment
Footer:  1 blocant · 1 avertizare
Drawer:  Probleme și avertizări — 7
```

**After**

```text
Sticky:  Configurarea necesită atenție · 1 blocant · 2 avertizări
Footer:  … · 1 blocant · 2 avertizări
         Următorul pas: Confirmă compoziția produsului.
Drawer:  Blocante — 1 · Avertizări — 2 · Informații — 4
```

**Why clearer:** one severity/count source; sticky and footer agree; drawer explains the larger “Informații” remainder instead of implying seven blockers.

## Frozen

Domain predicates, readiness, canSubmit, contracts, backend, Montaj IA, segmented/electrical contracts, pricing logic, Page 1 structure.

## Implementation order (after checkpoint)

1. Shared attention helpers on guidance model.  
2. Publish sticky issues via header overlay → footer guidance.  
3. Align sticky `summaryTitle` + drawer toggle/groups.  
4. Tests + live screenshots + worklog + isolated commit.
