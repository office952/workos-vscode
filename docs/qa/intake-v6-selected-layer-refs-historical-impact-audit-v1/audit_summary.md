# Intake V6 Selected Layer Refs — Historical Impact Audit (V1)

**Task:** INTAKE_V6_SELECTED_LAYER_REFS_HISTORICAL_IMPACT_AUDIT_V1
**Verdict:** **CONTROLLED_RESAVE_PILOT_RECOMMENDED**
**Accepted HEAD:** `9315fcf`
**Audit date:** 2026-07-10 UTC

---

## Script safety review

| Item | Result |
| --- | --- |
| Script (prior) | `docs/qa/intake-v6-selected-layer-refs-logo-role-handoff-v1/historical_impact_audit.py` |
| Script (this audit) | `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/run_historical_impact_audit.py` |
| Database mode | SQLite read-only URI (`file:...?mode=ro`) |
| Queries used | `SELECT` only on `intake_v6_workspaces`, `quote_snapshots_v2`, `quotes`, `orders`, `execution_plan` |
| Writes possible | **NO** |
| Safe to run | **YES** |

Confirmed absent: INSERT, UPDATE, DELETE, UPSERT, ORM commit/flush, workspace save, mutation HTTP, DB overwrite.

---

## Database target

| Field | Value |
| --- | --- |
| Engine | SQLite |
| Path | `backend/dev.db` (local development) |
| Config source | `DATABASE_URL` env + fallback to `backend/dev.db` |
| Environment | `development` |
| Identity | Local dev database — **not staging/production** |
| Read-only | Yes (`mode=ro`) |
| Active use | Unknown (file modified 2026-07-10) |
| Backup known | `dev.db.forensic.before_product_cleanup_20260630.db` |

**Caveat:** Production/staging impact is **unknown** until the same read-only audit is run there.

---

## Workspace counts

| # | Metric | Count |
| --- | --- | --- |
| 1 | Total Intake V6 workspaces | 147 |
| 2 | With `layer_role_setup` | 110 |
| 3 | Complete confirmed setup | 98 |
| 4 | With `svg.selected_layer_refs` key present | 1 |
| 5 | Missing persisted refs | 109 |
| 6 | Empty persisted refs (`[]`) | 0 |
| 7 | Confirmed `face` workspaces | 77 |
| 8 | Confirmed `printed_artwork` workspaces | 78 |
| 9 | Legacy `logo` alias workspaces | 0 |
| 10 | Unknown/unmapped confirmed roles | 0 |
| 11 | Derivation matches persisted | 1 |
| 12 | Derivation differs from persisted | 97 |
| 13 | Duplicate persisted refs | 0 |
| 14 | Invalid ref targets | 0 |
| 15 | Ambiguous layer identity | 0 |

---

## Classification breakdown

| Classification | Count |
| --- | --- |
| PRINTED_ARTWORK_LOGO_GAP | 78 |
| MISSING_PERSISTED_REFS | 19 |
| INCOMPLETE_SETUP | 12 |
| MATCH | 1 |
| STALE_PERSISTED_REFS | **0** |

**Key finding:** Drift is almost entirely **missing projection**, not **wrong persisted projection**.

---

## Risk classification

| Risk | Count |
| --- | --- |
| LOW | 31 |
| MEDIUM | 74 |
| HIGH | 5 |
| UNKNOWN | 0 |

### High-risk workspaces (downstream quote/order exposure)

| Workspace ID | Code | Classification | Quote | Order | Execution |
| --- | --- | --- | --- | --- | --- |
| `96009ff3-a20b-40d7-a8c7-540e48058526` | IV6-AA7F2532 | PRINTED_ARTWORK_LOGO_GAP | yes | yes | yes |
| `8887a6d0-8b97-4cb2-9ef5-43e193739996` | IV6-8D2ABB4E | PRINTED_ARTWORK_LOGO_GAP | yes | yes | no |
| `b13acdb3-d64b-44f8-9377-8f135bb54afe` | IV6-54F02286 | PRINTED_ARTWORK_LOGO_GAP | yes | yes | no |
| `10171236-4126-4556-baa3-3489b777c0ec` | IV6-294FF5D4 | PRINTED_ARTWORK_LOGO_GAP | yes | no | no |
| `4d920970-b4a5-4543-a1d3-2445d5669550` | IV6-47460D41 | MISSING_PERSISTED_REFS | yes | no | no |

Full detail: `high_risk_rows.json`

---

## Printed artwork / vector_logo impact

| Metric | Count |
| --- | --- |
| Workspaces with confirmed `printed_artwork` | 78 |
| Derive `vector_logo` on recompute | 78 |
| Lack persisted logo refs | 78 |
| Linked-template binding present | 0 |
| Logo finish confirmed | 30 |
| Remain blocked (binding and/or finish) | 78 |
| Letter-only misclassification (stale persisted) | 0 |

Logo handoff blockers (binding/finish) remain independent of this projection gap.

---

## Historical fixture check

**Workspace:** `22ef834d-f2d0-453b-a7a7-118928c98a39` (IV6-189D2F12)

| Check | Expected | Actual |
| --- | --- | --- |
| Persisted refs | absent | `null` |
| Derived projection | 4× `vector_litere` + 2× `vector_logo` | ✅ 6 refs |
| Row mutated | NO | NO |
| Classification | PRINTED_ARTWORK_LOGO_GAP | ✅ |
| Downstream exposure | none | none |
| Risk | MEDIUM | MEDIUM |

---

## Backfill decision

**Verdict: CONTROLLED_RESAVE_PILOT_RECOMMENDED**

Rationale:

- **Widespread but uniform drift:** 97/98 complete setups lack persisted refs; derivation is deterministic from canonical `layer_role_setup`.
- **No stale contradictions:** zero `STALE_PERSISTED_REFS`, zero duplicate/invalid persisted refs.
- **No ambiguous data:** zero unknown roles, zero ambiguous identities.
- **Natural re-save sufficient for most:** 74 MEDIUM + 31 LOW workspaces have no quote/order/execution linkage.
- **Pilot needed for 5 HIGH-risk:** workspaces already linked to Quote Snapshot V2 / Quote / Order need controlled re-save (not blind bulk backfill) so persisted projection aligns before further promotion work.
- **Bulk backfill not justified yet:** no evidence downstream consumed *incorrect* refs (none persisted); missing refs blocked promotion via read-time derivation guard.

### Proposed follow-up (plan only — no write code)

1. Re-run this audit on staging DB (read-only).
2. Pilot re-save on 5 HIGH-risk workspace IDs above; verify persisted refs after canonical layer-roles noop save.
3. Include fixture `22ef834d-…` in pilot for regression evidence.
4. Require DB backup before any write GO.
5. Defer bulk backfill until staging audit confirms same pattern and owner approves separate write task.

---

## Tests (pre-audit)

```
pytest tests/test_selected_layer_refs_derivation.py \
       tests/test_selected_layer_refs_runtime_capture.py \
       tests/test_product_truth_promotion_planner_service.py -q
```

| Field | Value |
| --- | --- |
| Passed | 29/29 |
| Failed | 0 |
| Duration | 3.25s |
| Exit | 0 |
| Hangs | none |

## Audit execution

| Field | Value |
| --- | --- |
| Duration | 0.159s |
| Rows audited | 147 |
| Rows changed | **0** |

---

## Artifacts

- `impact_counts.json`
- `representative_rows.json` (20 rows)
- `high_risk_rows.json` (5 rows)
- `run_historical_impact_audit.py`
- `execution_log.md`
