# Design checkpoint — Intake V6 Page 1 & composition clarity

**Date:** 2026-07-19  
**Baseline HEAD:** `bfddb1e`  
**Authority:** Owner GO — Page 1 + composition; Page 2 Montaj **frozen**

## 1. Current Page 1 structure

```
[Header + progress: Straturi → Configurare → Confirmare]
[Main]
  File confirm + SVG preview
  Layer decision cards (primary labels OK; secondary can show fill-*)
  Composition panel (full)
  Offer scope
  Advanced: metrici / geometrie
[Sticky operator panel]
  Confirm-all · upload · progress · warnings · color breakdown
  Helper: „Continuă la Review” (stale wording)
[Footer]
  Continuă la Configurare (+ disabled reason text, no aria-describedby)
[Inspect dialog legend]
  Raw `pseudo fill-*` via getOperatorLayerLabel
```

## 2. Proposed Page 1 structure

```
A. Fișier și analiză — file chip, status, counts (existing, tighten copy)
B. Elemente detectate — cards/legend with operator labels only
C. Elemente care necesită atenție — warnings/blockers (existing panel)
D. Rezumat pentru continuare — NEW concise handoff (ready / pending / blocked)
E. Pregătire Configurare — composition + offer scope (composition primary concise)
F. Detalii tehnice ale analizei — collapsed (metrics/geometry + raw ids)
```

## 3. Current composition summary

- Large expandable card above Page 2 tabs
- Defaults open when unconfirmed or has issues
- Linked PD segments dump (Role/binding/pricing lines) in primary details
- Template codes in details (OK)
- Source layers may still show raw ids when labels fail

## 4. Proposed composition summary

Primary (always scannable when collapsed):
- Tip compoziție (RO)
- Componente active (short list)
- Status: Propunere / Confirmată / Blocată
- Unresolved count or one blocker line

Expanded primary:
- Component cards (name + status only)
- Confirm CTA
- Visible blockers/warnings

Advanced (collapsed):
- Template codes
- Linked PD segments + readiness matrix
- Raw source layer ids

Default open: only when unconfirmed OR has blockers/warnings.  
When confirmed and clean: start collapsed (especially Page 2).

## 5. Always visible

- File identity / analysis status
- Pending/confirmed counts
- Unresolved role actions
- Blockers
- Footer Continue + reason when disabled
- Page 1 handoff summary line

## 6. On demand

- Raw `pseudo:` / fill hex / technicalKey
- Template codes
- Linked PD / binding status matrix
- Geometry metrics

## 7. Status hierarchy

| State | Operator label | Visual |
|-------|----------------|--------|
| Detectat automat | Detectat | muted |
| Propunere | Propunere sistem | amber soft |
| Confirmat | Confirmat | emerald |
| Necesită verificare | Necesită verificare | amber |
| Blocant | Blocant | rose |
| Ignorat | Decorativ / nefolosit | muted |

One primary status per layer card (icon OR short text, not both loud badges).

## 8. Page 1 completion message

Ready:  
`Analiza este pregătită. Pe Pagina 2 vei configura finisajele, iluminarea și montajul pentru componentele confirmate.`

## 9. Page 2 handoff message

Incomplete:  
`Mai sunt N elemente care necesită confirmare înainte de configurare.`

Blocked:  
`Nu poți continua până când rezolvi elementele marcate ca blocante.`

## 10. States

| State | UI |
|-------|-----|
| Normal | Cards with Propunere/Confirmat; handoff ready |
| Incomplete | Pending count + jump action; Continue disabled with reason |
| Warning | Warnings panel + footer drawer |
| Blocker | Visible outside advanced; Continue blocked |
| Confirmed | All-confirmed chip; composition can collapse |

## 11. Components moved/collapsed

| Component | Action |
|-----------|--------|
| Legend layer title | Use display-label helper (no raw pseudo fill) |
| Card secondary fill-* | Operator phrase without hex |
| Composition linked segments | Advanced accordion |
| „Guarded” | RO vocabulary |
| Helper „Review” | → „Configurare” |
| Handoff summary | New compact block in operator panel / main column |
| Continue button | aria-describedby → disabled reason |

## 12. Removed from primary / kept in diagnostics

- `pseudo fill-*` / `pseudo:…` as visible titles
- Linked PD pricing/quote/order/execution lines
- Raw binding English prose
- Hex fill tokens in secondary labels (kept under Detalii tehnice)

## Proceed

No owner ambiguity. Implement preferred structure. Montaj IA untouched.
