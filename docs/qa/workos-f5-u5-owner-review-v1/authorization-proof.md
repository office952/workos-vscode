# Authorization proof

| Actor | readiness GET | close POST | reopen | cost UI aggregates | margins |
|-------|--------------:|-----------:|-------:|-------------------:|--------:|
| admin | 200 | allowed | allowed | yes | yes |
| operator | 200 (after harden) | 403 job_close | 403 | minim note only | no |
| commercial/sales (UI other) | N/A UI null costs | fail-closed API | fail-closed | no panel | no |
| unknown | fail-closed | fail-closed | fail-closed | no | no |

Evidence: operator probe on `:8022` with `WORKOS_DEV_AUTH_USER_ID=c1-operator-user`; screenshots `roles/read-only.png`, `roles/unauthorized.png`.
