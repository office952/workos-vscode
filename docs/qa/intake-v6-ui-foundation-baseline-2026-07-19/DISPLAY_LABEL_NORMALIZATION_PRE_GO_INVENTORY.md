# Display label normalization — pre-GO inventory (read-only)

**Date:** 2026-07-19  
**Baseline HEAD:** `b1ba2ff`  
**Purpose:** Complete map before any rename pass. **No implementation until owner GO.**

---

## Target rule (future build)

```
SVG / analyzer truth
        ↓
single display-label layer
        ↓
Finisaje · Confirmare · (related Review chrome)
```

**Forbidden drift:** Finisaje translates one way, Confirmare another, Review a third.

**Canonical candidates already in repo (reuse, do not fork):**

| Helper | Path | Role today |
|--------|------|------------|
| `buildIntakeV6LayerDisplayLabel` / `resolveIntakeV6OperatorLayerTitle` | `intakeV6LayerDisplayLabel.ts` | Page 1 primary (Element N) |
| `getOperatorLayerLabel` + `isPseudoFillToken` | `intakeV4OperatorUiDisplay.ts` / display label | Safety net + composition |
| Artwork display path | `intakeV6ArtworkFinish.ts` (often uses `getOperatorLayerLabel`) | Safer than letter groups |

**Gap:** letter groups persist/display raw `layer.name` as `layer_name` without going through the display-label layer.

---

## Matrix — what the operator sees now vs should see

| Loc | Source field today | Ce vede operatorul acum | Ce ar trebui să vadă (primary) | Raw ID unde |
|-----|--------------------|-------------------------|--------------------------------|-------------|
| **Finisaje** letter cards | `group.layer_name` → `IntakeV6ReviewLetterGroupsSection` → `layerName` | `pseudo fill-*`, `Layer_x0020_*`, nume SVG | Label din display layer (ex. Element N / rol / culoare / „Fundal…” când e cunoscut) | Detalii tehnice card / accordion |
| **Confirmare** letter rows | `intakeV6ConfirmSummary` → `layerName` | același raw | **Același** display label ca Finisaje | technical / mono dacă e nevoie |
| **Confirmare** artwork rows | `row.layerName` | adesea OK (logo label) sau raw | același layer | technical |
| **Page 1 Straturi** | `buildIntakeV6LayerDisplayLabel` | Element N — … (curat) | neschimbat (frozen) | technical accordion |
| **Composition** source layers | `isPseudoFillToken` + `getOperatorLayerLabel` | RO / „Formă grafică…” under details | leave (frozen composition) | details |
| **Artwork Finisaje** cards | `display_name` / Vector Logo N | de obicei OK | leave unless leak proven | metadata expanded |
| **Legacy Face/Cant sections** | `group.layer_name` | raw (dacă ar fi montate) | N/A — not wired in ReviewStep | — |
| **Artwork-only decision** | `getOperatorLayerLabel` | mixed; poate TPL/EN | track separat (edge) | — |
| **Nesting / live calc tables** | `source_layer_name` | poate raw | out of this build unless primary | advanced |
| **DOM testids** | `group_key` | nu e copy vizibil | leave | N/A |

---

## Exact call sites to route through one display layer (when GO)

### Must-fix for the named build (Finisaje + Confirmare)

| # | File | Approx | Today | Action when GO |
|---|------|--------|-------|----------------|
| 1 | `IntakeV6ReviewLetterGroupsSection.tsx` | `layerName={group.layer_name}` | raw | Pass display label; keep `group_key`/raw for ids/testids |
| 2 | `IntakeV6LayerCardCollapsedHeader.tsx` | renders `layerName` | pass-through | No own mapping — parent supplies normalized label |
| 3 | `intakeV6LetterGroups.ts` | sets `layer_name: layer.name` | persists analyzer name | Prefer: keep persistence truth; **normalize only at render** (safer) OR store display separately — decide at GO (recommend render-time only) |
| 4 | `intakeV6ConfirmSummary.ts` | builds `layerName` from group | raw | Use same helper as Finisaje |
| 5 | `IntakeV6ConfirmOperationalSummary.tsx` | `Litere ${row.layerName}` | raw | Consume normalized summary field |

### Out of scope for that build (document only)

| # | File | Why |
|---|------|-----|
| A | `IntakeV6ReviewFaceLettersSection.tsx` / `CantLettersSection.tsx` | Legacy / unwired |
| B | `IntakeV6ProductCompositionPanel.tsx` | Composition frozen |
| C | `IntakeV6LayersRoleTable.tsx` | Page 1 frozen (already clean) |
| D | Montaj clusters | Montaj frozen |
| E | Analyzer / PD / bindings | Forbidden |

### Related leaks (rank later, not auto-included)

| # | File | Note |
|---|------|------|
| R1 | `IntakeV6ArtworkOnlyDecisionPanel.tsx` | English + template code on edge path |
| R2 | Confirmare title „Finish / Material” | EN section chrome |
| R3 | `IntakeV6NestingPreviewPanel.tsx` | `source_layer_name` in tables |
| R4 | Status OK vs Confirmat | Vocab consistency — separate from display names |

---

## Proposed single mapping (for GO discussion — not implemented)

**Primary operator title** = output of one function, e.g. extend:

`resolveIntakeV6OperatorLayerTitle(layer, index, report)`

or a thin adapter for letter groups:

`resolveIntakeV6LetterGroupDisplayLabel(group, report, index)` → uses same rules as Page 1:

1. If confirmed owner role implies named product sense → prefer role-aware short RO (without inventing false meaning)
2. Else Element N + color / formă grafică (existing Page 1 logic)
3. Never show `pseudo fill-*` / bare hex in primary
4. Unknown → `Element detectat — selectează / verifică` style, not fake “Litera A”

**Persistence:** keep `layer_name` / `group_key` as analyzer truth in payload.  
**Presentation:** only the display layer changes what the human reads.

---

## Acceptance criteria (when GO is granted)

1. One helper used by Finisaje letter cards + Confirmare letter rows  
2. No `pseudo fill-*` in those primary titles  
3. Page 1 / Montaj / composition / analyzer / contracts untouched  
4. Raw ids remain under technical disclosure or testids  
5. Reload / finish persistence unchanged  
6. Segmented CASE 1 still PASS  
7. Isolated commit only after green tests  

---

## Current recommendation

**Do not implement yet.**  
Baseline is frozen at `b1ba2ff`.  
This inventory is the entry ticket for the next GO.
