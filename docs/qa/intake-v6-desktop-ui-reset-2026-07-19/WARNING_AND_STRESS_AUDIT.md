# Warning and Stress Audit — Intake V6 Desktop

**Runtime workspace:** `29472e22-5fe1-4e8d-af66-f9ab75d5fe32` (ACM letters)  
**Viewport:** 1440×1000  
**Baseline:** `9f0efa0`

## Classification key

| Class | Meaning |
|-------|---------|
| Real blocker | Operator cannot honestly proceed until resolved |
| Actionable warning | Should act, but may continue with risk |
| Informational | Context; no forced action |
| Positive confirmation | Success / OK / updated |
| Technical diagnostic | Registry, IDs, readiness bits |
| Duplicate status | Same truth already shown elsewhere |
| Stale/irrelevant | Mentions unrelated step or jargon |

## Inventory of warning-like surfaces

| ID | Visible message (summary) | Class | Act? | Where act? | Now? | Near cause? | Too large? | Duplicates? | False urgency? | Disposition |
|----|---------------------------|-------|------|------------|------|-------------|------------|-------------|----------------|-------------|
| W01 | Header “Stare sistem: necesită verificare” | Informational / Unknown | Unclear | Outside Intake | Maybe | No | Medium | Global shell | **FALSE_URGENCY** | Demote; not Intake blocker |
| W02 | Produs badge “Necesită confirmare” | Actionable warning | Yes | Confirm CTA in same card | Now | Yes | Small | Footer next-step | Keep badge; reduce red cascade |
| W03 | Blocker banner “2 blocante · 1 avertizare” | Mix: Real blockers + summary | Yes | Footer / expand list | Now | Partial | **Very large** | Footer + drawer | Stress overload | Compact sticky chip; expand for list |
| W04 | Banner “Următorul pas este în footer” | Informational + Detached | Yes | Footer | Now | **No** (CTA is top) | Medium | Footer | Confusing | Remove; point to owning CTA |
| W05 | “Vezi detalii tehnice și diagnostic” | Technical diagnostic link | Optional | Page bottom / drawer | Later | No | Link OK | Drawer inventory | Mild | Keep in disclosure |
| W06 | Pricing amber: confirm composition before priced dry-run | Actionable warning / Duplicate | Yes | Produs CTA | Now | **No** (right rail) | Medium | W02/W03/footer | Medium | Local note under Produs; quiet rail |
| W07 | “Tarife lipsă — Accesorii montaj…” | Actionable warning | Maybe Pricing | Pricing registry | Later | Rail OK | Medium | Line details | Legitimate | Keep compact on rail |
| W08 | Footer “Configurare incompletă · 2/3 · 2 blocante” | Duplicate status | Yes | Footer next | Now | Yes | Large | W03 | High | Single status spine |
| W09 | Footer “Următorul pas: Confirmă compoziția…” | Guidance (correct) | Yes | Top CTA | Now | Detached from CTA | Medium | W04 | None if alone | Keep as sole next-step |
| W10 | Drawer “2 blocante · 1 avertizare · 7 informații” | Duplicate inventory | Optional | Drawer | Later | OK | Small | W03/W08 | Low | Keep drawer only |
| W11 | Cant “necesită valori obligatorii…” (when present) | Real blocker | Yes | Finisaje cant | Now | Yes when on Finisaje | Medium | Banner list | Legitimate | Local-first near Cant |
| W12 | Autosave “Preturi si materiale actualizate” | **Positive confirmation** | No | — | — | Near save footer | Small | — | **FALSE_URGENCY if amber** | Emerald/neutral success; never alert chrome |
| W13 | Layer confirmed emerald text | Positive confirmation | No | — | — | On card | Small | — | OK | Keep quiet emerald |
| W14 | File “Fișier recunoscut” emerald chip | Positive confirmation | No | — | — | Preview | Small | — | OK | Keep |
| W15 | Montaj “Propunere” yellow chip | Actionable warning | Yes | Fundal confirm | Now | Near panel | Small | Segmented panel | OK | Keep local |
| W16 | Inactive prep notes (slate) | Informational | No | — | — | Inside section | Medium empty | — | Low | Collapse when inactive |
| W17 | Service corner inactive note | Informational / DETACHED_HELPER | No | — | — | Beside cable field | Small | — | Low | Show only when ACP + relevant |
| W18 | Product System badge/link | Technical diagnostic | Optional | Product System app | Later | On Montaj | Small | Template ID | Leak | Disclosure only |
| W19 | SVG hash / contour IDs in ACP box | Technical diagnostic | No | — | — | Nested ACP | Medium | — | Leak | Disclosure |
| W20 | Confirmare collapsed: blockers only in status tile | Real blockers hidden | Yes | Expand summary | Now | Buried | — | — | **Dangerous calm** | First-paint must show blockers |

## Stress pattern (observed)

On a single Finisaje/Montaj viewport the operator sees simultaneously:

1. Global shell amber (W01)  
2. Produs amber badge (W02)  
3. Full-width rose banner (W03–W05)  
4. Pricing amber paragraph (W06)  
5. Pricing missing-rate chip (W07)  
6. Footer incomplete bar (W08–W09)  
7. Footer inventory strip (W10)

**Same “confirm composition” truth is repeated ≥4 times** with alert chrome. That is the core false-stress engine.

## Required stress policy (proposal — not implemented)

1. **One attention spine:** footer sticky counts + next step.  
2. **One local CTA for the current required action** (e.g. Confirmă compoziția).  
3. **Blocker banner becomes compact** unless expanded; never both huge banner + huge footer.  
4. **Positive confirmations never use amber/rose.**  
5. **Pricing warnings stay on rail**, not full-page red.  
6. **Technical diagnostics never use alert chrome.**

## Consequences

| If we keep as-is | Operator stress stays high; product decisions stay below fold |
|------------------|------------------------------------------------------------------|
| If we hide blockers | Truth regression — forbidden |
| If we demote duplicates only | Stress drops; truth preserved |
