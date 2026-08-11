# PERFORMANCE_REGRESSION

No frontend refetch-domain changes in this slice.

Slice 1 still holds:

- face/backing/lighting → 4 offer-critical groups
- production/task GETs → 0 while diagnostic drawer closed

Verified: `intakeV6ReviewRefetchDomains.test.ts` → 12 passed.
