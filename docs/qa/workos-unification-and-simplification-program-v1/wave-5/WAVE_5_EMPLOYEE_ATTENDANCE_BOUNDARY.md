# Wave 5 — employee vs attendance

| Question | Answer |
|----------|--------|
| attendance = work? | **NO** — default-present + exception events |
| assigned = working? | **NO** on HR pages (assignment is Execution) |
| session = attendance? | **NO** — sessions are shop-floor |
| employee record = master? | **NO** — records = dossier UX on live names |

`/attendance` class: **ATTENDANCE_TRUTH**.  
`/attendance/effects`: pipeline into attendance, not payroll.

**ATTENDANCE_SESSION_SEPARATION = CLEAR**  
**ATTENDANCE_RBAC_RELATION = MIXED** — manager UI open / backend GET 403; operator nav absent / backend GET 200. DEV admin bypass is not production role proof. See [`WAVE_5_ATTENDANCE_RBAC_ANALYSIS.md`](./WAVE_5_ATTENDANCE_RBAC_ANALYSIS.md). Do not fix RBAC here.
