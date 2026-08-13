# Wave 2 evidence reconciliation

Two RT logs, one SoT story.

| Log | Shots | Surfaces | Role |
|-----|------:|---------:|------|
| `runtime/rt-capture-log.json` | 001–106 | 42 | original Wave 2 |
| `runtime/rt-gap-closure-log.json` | 200–413 | 56 | gap closure |

## Screenshot manifest corrections

| Old path / tab | Was labeled | Actual | Disposition |
|----------------|-------------|--------|-------------|
| `…/layers/` seq 005+ | Straturi | **Configurare** (Pasul 2) | `SUPERSEDED_MISLABEL` — keep file, do not cite as Straturi |
| `…/straturi/` seq 202+ | — | **Straturi** (Pasul 1) | CANONICAL |
| `…/review-Panou-carcasa/` | — | Panou / carcasă selected | CANONICAL |

No remaining file is cited as Straturi unless `ACTUAL_STEP=Straturi` or folder `straturi/`.

## Interaction inventory

| Surface | After gap closure |
|---------|-------------------|
| `/intake` | list + row + edit followed; mutating CTAs still SNR |
| V6 Straturi | RECONCILED (proven) |
| V6 Configurare Finisaje/Iluminare/Montaj | original capture |
| V6 Panou / carcasă | RECONCILED |
| V6 Confirm | original; handoff disabled photographed |
| `/orders` + detail | admin original + sales gap closure both themes |
| `/clients` + workspace tabs including stubs | RECONCILED |
| Hover/focus | sample RECONCILED |
| Browser back | RECONCILED |

**MISLABELED_EVIDENCE_REMAINING = 0**
