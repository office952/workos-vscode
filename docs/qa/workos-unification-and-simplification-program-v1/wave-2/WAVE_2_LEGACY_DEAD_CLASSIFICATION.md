# Wave 2 — legacy / dead classification

Source: `lane-g-legacy-dead/CLASSIFICATION.md`. Classify-don’t-delete. Ugly ≠ dead.

| Artifact | Class | Evidence |
|----------|-------|----------|
| `/intake` list | ACTIVE | Shell Cereri; 55 live rows |
| `/intake-v6/:id/operator` | ACTIVE | Opened from list; real workspace |
| `/intake/:id` | COMPAT | Redirect to V6; not walked as UI |
| `/intake-v6/operator` bootstrap | ACTIVE / dangerous | Creates workspace — **not opened** |
| `IntakeDetail.tsx` | LEGACY | On disk, not routed |
| `/intake-v2` E2E | AUDIT_ONLY | No App route |
| FE `/intake-v4` routes | REMOVE_CANDIDATE_ONLY | No App routes; E2E residue |
| `intakeV6` re-export `intakeV4*` | COMPAT | Runtime V6, V4 filenames |
| `intakeV4OperatorRoutes.ts` | DUPLICATE_CANDIDATE | Zero production imports |
| Client stub tabs Facturi/Documente/Note/Timeline | PLACEHOLDER | Opened; “nu este implementat”; write CTAs disabled |
| Orders “Înghețat” × 27 | ACTIVE | Snapshot lock language; not dead |
| Flux stage “Produse” | DUPLICATE_CANDIDATE (IA) | Inserts Product System into commercial strip |

**LEGACY_REMOVE_CANDIDATE_COUNT = 1** (`/intake-v4` FE residue). No deletion performed or recommended as a Wave 2 action.
