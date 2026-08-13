# Wave 2 hover / focus sample (F)

Representative primitives only. Admin × light + dark. Not exhaustive CSS-state coverage.

| Primitive | HOVER | FOCUS | VISIBLE_FOCUS light | VISIBLE_FOCUS dark | THEME_PARITY | ISSUE |
|-----------|-------|-------|---------------------|--------------------|--------------|-------|
| nav item (Cereri) | CAPTURED | CAPTURED | YES | YES | YES | none |
| list row | CAPTURED | CAPTURED | YES | YES | YES | none |
| search input | CAPTURED | CAPTURED | YES | YES | YES | none |
| primary CTA (Deschide Intake V6) | CAPTURED | CAPTURED | WEAK_OR_NONE | WEAK_OR_NONE | YES | weak ring both themes |
| secondary button | CAPTURED | CAPTURED | WEAK_OR_NONE | WEAK_OR_NONE | YES | weak ring both themes |
| V6 review tab | CAPTURED | CAPTURED | WEAK_OR_NONE | WEAK_OR_NONE | YES | weak ring both themes |
| disabled handoff CTA | CAPTURED | CAPTURED | YES | YES | YES | disabled remains readable |

Files: `runtime/screenshots/admin/{light,dark}/_intake/hover-focus/` (seq 293–306, 400–413).

**HOVER_FOCUS_SAMPLE_COMPLETE = YES**

Systemic note (not a Wave 2 fail): primary/secondary/tab focus rings are weak in both themes. Day-mode shell contrast remains the Wave 1 systemic issue.
