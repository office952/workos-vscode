# Design checkpoint — Intake V6 Page 2 IA (before code)

**Date:** 2026-07-19  
**Baseline HEAD:** `5511a6b`  
**Authority:** `docs/architecture/INTAKE_V6_COMPLETE_UI_UX_AND_FLOW_AUDIT.md` + owner GO

## 1. Current Page 2 structure

```
[Composition panel] [Offer scope summary]
[ReviewOperatorBlockerBanner]  ← not sticky
[Tabs: Finisaje | Iluminare | Montaj]
Finisaje → letter/artwork finishes
Iluminare → LED + subsection "Electrică" (PSU)
Montaj (flat dump):
  ownership notes → scope → prep → solution → ACP → face modules
  → segmented → electrical → fixing → legacy corner → cable → site
[Sticky live calc] [Sticky footer Continuă]
```

## 2. Proposed Page 2 structure

```
[Composition panel — compact when unconfirmed]
[Offer scope summary — compact]
[STICKY FinalBlockerSummary — actionable, tab/section targets]
[Tabs: Finisaje | Iluminare și surse | Montaj]
Finisaje → unchanged core (Configurare produs)
Iluminare și surse → LED + "Alimentare LED / surse" (PSU)
Montaj:
  A. Compoziție / readiness (short status if still needed)
  B. Fundal și carcasă (cluster):
       ACP shell essentials → Segmented → 220V per panel
  C. Montaj comercial (collapsed when scope inactive)
  D. Avansat (collapsed): ownership notes, fixing, process, legacy corner rules
```

## 3–7. Component disposition

| Component | Action |
|-----------|--------|
| Composition panel | Stay above tabs; not freeze tab nav |
| Finisaje sections | Stay |
| Lighting + PSU | Stay on tab 2; rename labels |
| SegmentedBackgroundPanel | Move into Fundal cluster |
| SegmentedElectricalPanel | Move into Fundal cluster (same story) |
| Mounting scope / prep / site | Montaj comercial (collapsible) |
| ACP product config (essentials) | Inside Fundal when ACM |
| ACP local face modules | Progressive / advanced when noisy |
| Ownership notes | Avansat collapsed |
| Fixing / process / volum Al | Avansat collapsed |
| Legacy service corner | Show only when NOT segmented CONFIRMED; demote note when CONFIRMED |
| Operator blocker banner | Become sticky + actionable summary |
| Live calc | Stay sticky right (unchanged behavior) |

## 8. Sticky blocker

- Position: below offer scope, above tab nav (sticky top under header chrome)
- Lists only real final-confirmation blockers with RO actions + tab id
- Warnings separate (non-blocking tone)
- Does not disable tab buttons

## 9–13. States

| State | UI |
|-------|-----|
| Normal | Clusters show primary decisions |
| Incomplete/draft | Status badges on clusters; sticky lists gaps |
| Warning | Amber, not in blocker count |
| Blocker | Rose sticky + disabled footer Continuă |
| Confirmed | Cluster summary compact; details collapsed |

## 14. Operator path

Page1 roles → Page2 Finisaje → Iluminare și surse → Montaj Fundal (confirm assembly + 220V) → resolve sticky items → Continuă Confirmare.

## Figma

Existing files (`0CDPIuqoaZ1OQgNnvNyl1F`, `911Q6oRKcEursrRoT4Qj0h`) predate Fundal cluster — reuse hierarchy principles only; **runtime screenshots** are acceptance.

## Proceed

No owner-level ambiguity remains. Implement preferred structure above.
