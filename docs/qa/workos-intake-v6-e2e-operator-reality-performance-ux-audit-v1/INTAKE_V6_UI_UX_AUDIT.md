# INTAKE_V6_UI_UX_AUDIT

Viewport: desktop browser · Screenshots: `screenshots/step1-straturi.png`, `step2-configurare-finisaje.png`, `step3-confirmare.png`

## Overall

**UI_UX_STATUS = DEGRADED / HEAVY** — operator can configure, but hierarchy mixes offer/cost/diagnostic; feedback for save vs price recalc is weak; Step 2 density high.

## Region recommendations

| Region | Action |
|--------|--------|
| App left nav (full WorkOS shell) | KEEP (product) but competes with workspace — accept |
| Step progress Straturi/Configurare/Confirmare | KEEP |
| Step 2 domain tabs (Finisaje/Iluminare/Panou/Montaj) | KEEP |
| Letter group summary row (Față/Cant/Spate) | KEEP — primary |
| “Detalii tehnice despre finisaj” accordion | **HIDE_BY_DEFAULT** / MOVE_TO_DIAGNOSTIC |
| “Deschide diagnostic tehnic” | MOVE_TO_DIAGNOSTIC |
| Right Ofertă rail | KEEP — clarify official vs estimates |
| “CE BLOCHEAZĂ / Tarife lipsă” in offer rail | **SIMPLIFY** — do not compete with gross |
| ACM provisional block | SIMPLIFY / separate from Ofertă client |
| Commercial adjustments drawer | KEEP |
| Footer warnings strip | SIMPLIFY |
| Confirm checklist | KEEP — fix honesty drift |
| Confirm Ofertă card | KEEP |

## Operator questions

| Question | Answer now |
|----------|------------|
| Know what changed? | Partial — selector updates; money lag |
| Know save finished? | Weak — no strong save ack |
| Know price recalc finished? | Weak — total may stale then jump; no explicit “recalculating” |
| Distinguish material / finish / technical / cost / client price? | **No** — conflated labels + dual blockers |
| Diagnostic leakage? | **Yes** — technical accordion + SVG ids + diagnostic entry on primary path |

## Scanability

- Step 2 first viewport: tabs + element row + technical accordion + offer rail — **dense**
- Sticky footer + left nav + right rail → reduced form width
- Confirm clearer than Review for hierarchy
