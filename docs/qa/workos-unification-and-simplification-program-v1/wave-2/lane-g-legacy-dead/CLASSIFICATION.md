# Lane G — classify only

| Artifact | Class | Evidence |
|----------|-------|----------|
| `/intake` list | ACTIVE | Shell Cereri; 55 live rows |
| `/intake-v6/:id/operator` | ACTIVE | Only operator workspace; opened from list |
| `/intake/:id` | COMPAT | Redirect to V6; not walked as UI |
| `/intake-v6/operator` bootstrap | ACTIVE / dangerous | Creates workspace — not opened |
| `IntakeDetail.tsx` | LEGACY | On disk, not routed |
| `/intake-v2` E2E | AUDIT_ONLY | No App route |
| FE `/intake-v4` routes | REMOVE_CANDIDATE_ONLY | No App routes; E2E residue |
| `intakeV6` re-export `intakeV4*` | COMPAT | Runtime V6, V4 filenames |
| `intakeV4OperatorRoutes.ts` | DUPLICATE_CANDIDATE | Zero production imports |
| Client stub tabs Facturi/Documente/Note/Timeline | PLACEHOLDER | Opened in gap closure; copy says module not implemented; CTAs disabled |
| Orders “Înghețat” × 27 | ACTIVE | Snapshot lock language; not dead |
| Flux stage “Produse” | DUPLICATE_CANDIDATE (IA) | Inserts Product System into commercial strip; not a dead route |

No deletion. Ugly ≠ dead. Unlinked ≠ dead.
