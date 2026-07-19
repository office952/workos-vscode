# Design Checkpoint — Configurator Letter Pilot

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `ee93b19`  
**Mode:** Checkpoint before code — volumetric letters Finisaje + Iluminare only

## Pre-flight

| Item | Value |
|------|--------|
| HEAD | `ee93b19` |
| Foreign WIP | Present — untouched |
| Pilot product | Litere volumetrice |
| Frozen | Montaj IA · Page 1 · segmented · electrical contracts · backend · domain |

---

## 1. Current letter UI structure

```text
Finisaje tab
├─ SectionShell "Finisaje pe layer"
│  ├─ LetterGroupsSection (Vector Litere)
│  │  └─ cardCompact → LayerCardShell[]
│  │     ├─ collapsed: Față / Cant / Spate summaries
│  │     └─ expanded: Zone Față → Cant → Spate (inputs)
│  └─ ArtworkFinishSection (Vector Logo) — same pattern
└─ TechnicalDetailsAccordion (finish ownership tokens)

Iluminare tab
├─ contract iluminare section (if any)
└─ SectionShell → ReviewLightingSection
   ├─ LED toggle + perimeter (result) mixed
   ├─ Iluminare inputs + inline module totals (mixed)
   ├─ PSU inputs + allocation readout (mixed)
   └─ Accordion "Detalii calcul LED"
```

Legacy Face/Cant split sections exist but are **not mounted** in ReviewStep.

---

## 2. Problems found

| Problem | Detail |
|---------|--------|
| Tiny type | Widespread `text-[10px]` / `11px` on letter cards and lighting |
| Nesting | Section → cardCompact → LayerCardShell → zones (4 frames) |
| Weak anatomy | Față/Cant/Spate exist but feel like form rows, not letter parts |
| Input/result mix | LED module counts + PSU watts on L1 beside selects |
| Technical L1 | Ownership mono tokens; artwork `group_key` / SVG source lines |
| Scope risk | Changing global `v6.page` would hit Montaj — **out of bounds** |

---

## 3. Proposed pilot structure

```text
LETTER (per layer card)
┌ Anatomy header: icon + Element label + status
├ FACE   — decisions (finish/color)     [input]
├ SIDE   — decisions (cant)             [input]
├ BACK   — decisions (backing)          [input]
└ Technical (collapsed)                 [L4]

LIGHTING (section)
├ Decisions: LED on/off, system, color, PSU watts  [input]
└ Results: modules, perimeter, PSU required        [read-only panel]
```

Fit existing IA (tabs unchanged). No Montaj touch.

---

## 4. Components reused

- `IntakeV6ReviewLetterGroupsSection` / `IntakeV6ArtworkFinishSection`
- `IntakeV6LayerCardShell` / collapsed layout
- `IntakeV6ReviewLightingSection`
- `IntakeV6TechnicalDetailsAccordion`
- `operatorStatusSemanticRo` / guidance (unchanged)
- Lucide icons (already in repo)

---

## 5. Components changed (scoped)

| File | Change |
|------|--------|
| `intakeV6Presentation.tsx` | Add **pilot-scoped** tokens (`v6Pilot`) — do not rewrite `v6.page` |
| `layerCardCollapsedLayout.ts` | Uplift summary type; anatomy column headers |
| `IntakeV6ReviewLetterGroupsSection.tsx` | Anatomy header + icons; kill 10px; clearer FACE/CANT/BACK |
| `IntakeV6ArtworkFinishSection.tsx` | Same anatomy chrome; demote SVG/group_key to technical |
| `IntakeV6ReviewLightingSection.tsx` | Input vs Result split; uplift type; RO light labels |
| `IntakeV6ReviewStep.tsx` (Finisaje only) | Soften ownership token block presentation (still collapsed) |
| `reviewFieldLayout.ts` | Slight select/label uplift used by letter/lighting fields |

---

## 6. Typography changes (pilot scope)

| Role | From | To |
|------|------|-----|
| Cluster title (Vector Litere) | 10–12px | 16–18px (`v6Pilot.clusterTitle`) |
| Anatomy zone (Față/Cant/Spate) | 12px zoneTitle | 14–15px |
| Field labels | 12px | 13–14px |
| Body / selects | 11–12px | 13–14px |
| Collapsed summaries | 11px | 13px |
| Helper | 10–11px | 12px |
| Technical | 10px | 11px only inside accordion |

**No `text-[10px]` on letter/lighting decision surfaces.**

---

## 7. Spacing changes

- Letter zone padding: slightly more vertical gap between FACE/CANT/BACK
- Lighting: gap between Decisions block and Results panel
- No page-margin rewrite (avoids Montaj layout shift)

---

## 8. Product anatomy representation

Collapsed card: three columns with icons — **Față · Cant · Spate**  
Expanded: labeled zones with same icons (Box / Panel / Layers metaphors via Lucide)  
Lighting: Lightbulb + Power icons on decision/result headers  

Not a full 3D silhouette (too large for pilot); anatomy grouping is the principle.

---

## 9. Input/result separation

**Lighting:** move module totals + PSU required/allocation into `Results` panel (read-only chrome). Keep selects in Decisions. Keep detailed calc accordion.

**Finisaje:** collapsed summaries remain results; expanded zones remain inputs. Demote print-roll math notes under helper or technical.

---

## 10. Technical disclosure location

| Content | Location after |
|---------|----------------|
| Finish ownership tokens | Stay in Finisaje accordion; remove mono shout from body emphasis |
| Artwork group_key / SVG source | Move into technical accordion or title tooltip only |
| LED calc details | Existing accordion — keep |

---

## 11. What remains unchanged

- Tab IA (Finisaje / Iluminare / Montaj)
- Montaj components and contracts
- Page 1
- Domain predicates / readiness / guidance model logic
- Status vocabulary IDs
- Backend / analyzer / segmented / electrical
- Global app theme / CSS frameworks
- Pricing rail wiring (demotion deferred — out of letter pilot)

---

## Go / No-Go

**GO** for scoped presentation pilot as above.  
**STOP** if any change requires finish persistence or lighting formula edits.
