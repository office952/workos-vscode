# CP1 — Artificial vs real blockers

| Blocker | Before | After | Classification | Reason |
|---------|--------|-------|----------------|--------|
| AMBALARE_COMMERCIAL_RULE | CPP `ambalare` blocked | demoted; line warning | AI_DEFAULT_ACTIVE | packaging band AI |
| PACKAGING MISSING_OWNER_FORMULA | unresolved labor | qty-key via AI band | AI_DEFAULT_ACTIVE | size category |
| ELECTRICAL OPERATION_ONLY | unresolved | qty-key / catalog+AI meta | AI_DEFAULT_ACTIVE | min+PSU formula |
| LED_ASSEMBLY_TIME_NOT_BOUND | warning | INFORMATIONAL retained | WARNING | no time-primary; module qty remains |
| PREPRESS OPERATION_ONLY | unresolved | unchanged | WARNING / real skip | no safe qty basis → no AI invent |
| ACM_TREATMENT_COMMERCIAL_BLOCKED | blocked | **retained** | BLOCKER | structural / owner rates |
| ACM shell FOLD/MOUNT missing formula | unresolved | AI panel labor m² | AI_DEFAULT_ACTIVE | shell only |
| MISSING_CATALOG_RATE (bonding/paint Volum Al) | commercial gap | retained | BLOCKER / missing catalog | not invent rates into catalog |
| MONTAJ_COMMERCIAL_RULE (VL) | present | retained | WARNING/BLOCKER | not in AI packaging/elec/LED scope |

## Eligible for AI default

Safe: packaging, electrical (min+PSU), LED per module, ACM panel fold/mount shell labor.

Unsafe / skip: PREPRESS (no qty), ACM face treatments, inventing productivity/time.
