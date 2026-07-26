# Intake V6 — Count Channel Consolidation

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `46ead84`  
**Mode:** Frontend presentation only

## Verdict

**PASS.** Sticky, footer spine, and drawer share one attention inventory from the Operator Guidance Model. Counts no longer contradict (“3 elemente” vs “1 blocant” vs “Probleme — 7”).

## Checkpoint

See `COUNT_CHANNEL_CONSOLIDATION_CHECKPOINT.md`.

## Selected model

```text
Sticky inventory (buildOperatorBlockerBannerDisplay.issues)
        ↓ publish overlay.attentionIssues
Operator Guidance Model
        ├── nextAction → Footer
        ├── countsLabel / stickySummaryTitle → Sticky + spine
        └── drawerToggleLabel + groups → Drawer
```

Severity: Blocant · Avertizare · Informativ (existing vocabulary).

## Live proof (IV6-15CCCD91)

| Channel | After |
|---------|--------|
| Sticky | Configurarea necesită atenție · 3 blocante · 1 avertizare |
| Footer spine | … · 3 blocante · 1 avertizare · Următorul pas: … |
| Drawer toggle | 3 blocante · 1 avertizare · 7 informații |

Information remainder is explicit — not presented as blockers.

## Files

- `intakeV6OperatorGuidance.ts` (+ tests) — inventory + labels
- `intakeV6OperatorBlockerBannerDisplay.ts` — sticky title from guidance
- `intakeV6WorkspaceHeaderStatus.ts` — `attentionIssues` overlay
- `IntakeV6ReviewStep.tsx` — publish sticky issues
- `IntakeV6OperatorWorkspaceFooter.tsx` (+ tests) — drawer from guidance
- Banner component vocabulary (Blocant / Avertizare)

## Tests

36 Vitest PASS (guidance, banner display, sticky UI, footer, step-scoped).

## Frozen

Domain / readiness / canSubmit / contracts / backend / Montaj IA / segmented·electrical contracts / pricing logic.
