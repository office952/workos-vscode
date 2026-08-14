# Wave 5 — evidence reconciliation (gap closure)

Do not duplicate Wave 5 primary shots.

| Ledger | Status |
|--------|--------|
| Initial RT | `runtime/rt-capture-log.json` — 54 surfaces / 170 shots / scroll fail=0 |
| Gap RT | `runtime/rt-gap-closure-log.json` — 15 surfaces / 18 shots / scroll fail=0 |
| Attendance probe | `runtime/manager-attendance-probe.json` — manager GET 403 |
| New shots | `runtime/screenshots-gap-closure/` only |
| Prior Wave 5 shots | unchanged; not recaptured |

## Screenshot manifest

| Set | Count | Reconciled |
|-----|-------|------------|
| Wave 5 initial | 170 files = log `shots` | YES (unchanged) |
| Gap closure | 18 files = log `shots` | YES |
| Combined targeted | 188 | YES |

`SCREENSHOT_MANIFEST_RECONCILED = YES`  
`MISLABELED_EVIDENCE_REMAINING = 0` (the “no row link” label is corrected to selector miss)

## Role / theme on new surface

| Role | Light | Dark |
|------|-------|------|
| admin | row-click + 4 tabs | deep-link + 4 tabs |
| manager | deep-link + 4 tabs | not required (same page as admin dark) |
| sales / operator | denied redirect | n/a |

`LIGHT_DARK_COMPLETE = YES`  
`ROLE_COVERAGE_RESOLVED = YES` (MATCH 5/5)

## Product / DB

`PRODUCT_CODE_CHANGES = 0` · `OWNER_DEV_DB_MUTATIONS = 0` · all listed domain mutations = 0.
