# Design checkpoint — Finisaje SURFACE_FINISH ownership cleanup

**Date:** 2026-07-19  
**Baseline HEAD:** `51ea07a`  
**Authority:** Owner GO — Finisaje ownership demotion only  
**Frozen:** Page 1, composition, Montaj IA, segmented, electrical, sticky blocker

## 1. Current Finisaje structure

```
[Tabs: Finisaje | Iluminare și surse | Montaj]
Finisaje panel:
  [optional ArtworkOnlyDecision]
  [Detalii ownership finisaje] ← hint leaks SURFACE_FINISH / RETURN-CANT when collapsed
  [optional finisaje_fields fallback]
  [Finisaje pe layer: Față → Cant → Spate + Vector Logo]
```

## 2. Current SURFACE_FINISH accordion contents

Static JSX prose (not PD/template-bound):
- `SURFACE_FINISH`, `RETURN-CANT`, `WORKSPACE`, sold `FINISH` deferred notes
- No inputs, no confirm, no gate

## 3. Required by operator

- Zone finish controls (Față / Cant / Spate / Vector Logo)
- Material/catalog selections in those controls
- Incomplete/pending signal (existing tab badge / blockers)
- Owner/admin decision only when a real gate exists elsewhere (not this accordion)

## 4. Diagnostic only

- Ownership responsibility map
- Raw domain enums
- “șablon ≠ finisaj”, sold chip deferred notes

## 5. Duplicate information

Accordion restates concepts already labeled on Față/Cant cards (finisaj vizibil vs cant).

## 6. Proposed primary summary

No new card. Primary = existing **Finisaje pe layer** section + pending badge.  
Remove ownership from the top of the tab.

## 7. Proposed advanced disclosure

After finish controls, single collapsed accordion:

- Title: `Detalii tehnice despre finisaj`
- Collapsed hint (RO, no raw tokens): `Opțional — sursă de adevăr și mapări interne`
- Expanded: short RO meaning + labelled raw tokens for diagnostics
- Keep `testId="intake-v6-finish-ownership-note"` for continuity

## 8–12. States

| State | Presentation |
|-------|----------------|
| Normal | Controls primary; technical collapsed |
| Incomplete | Existing pendingFinisaje / blockers (unchanged) |
| Warning | Existing warnings (unchanged) |
| Owner-decision | Not invent from this accordion (no owner action inside) |
| Confirmed | Existing confirm flows (unchanged) |

## 13. Accessibility

Reuse `IntakeV6TechnicalDetailsAccordion` (`aria-expanded`, clear title). No raw tokens in collapsed hint/title.

## 14. Components affected

- `IntakeV6ReviewStep.tsx` (Finisaje panel ownership block only)
- `intakeV6OperatorVocabulary.ts` (+ tests)
- New vocab placement guard test
- New live E2E + screenshots/worklog

## 15. Explicitly frozen

Page 1 · composition panel · Montaj ownership / Fundal / comercial / Avansat · segmented · electrical · sticky blocker architecture
