# Machine actual feasibility

**Conclusion:** CONDITIONAL / unavailable — not inventable in V1.

Runtime lacks confirmed machine instance + actual usage duration + dated machine cost policy.
Forbidden fallbacks: `workcenter.rate_per_hour`, commercial tariff, planned duration as actual, capacity as utilization.

When plan/task declares `machine_id` (etc.): `applicable_optional` + `machine_actual_not_captured`.
Otherwise: `not_applicable` via `machine_not_applicable_by_job_profile`.
