# WORKOS_VOLUMETRIC_LETTERS_AUTHORITY_INSTANCE_PLACEMENT_V1 — Build 1 worklog

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Scope | A — authority + lifecycle + quantities + placement minimal |
| Status | Implemented — awaiting owner review |
| AcmPanel closed HEAD | `56217a9` — not reopened |

## Verdict (implementer)

**CONDITIONAL PASS for owner review** — core authority model landed with tests + dry runtime proof. No Offer/Order/Execution writes. ReviewStep net ~+1 line. Split/merge join-by-`group_key` rules documented (confirmed orphans preserved; new keys mint new UUIDs).

## Logic implemented

```text
letter_group_instances[]  → write authority
UUID                      → identity
group_key                 → artwork/analysis join
artwork                   → suggest; confirmed survives fill drift
instance lighting         → authority after hydrate (flags from global; LED count stays workspace until per-group set)
quantity builder          → sole V6 commercial qty resolver for CPP measurements
CostEngine                → legacy parallel flag only
component_placements[]    → persist minimal relation
letter_group_finishes[]   → one-way projection
```

## Helpers (ownership)

| Helper | Location | Role |
|--------|----------|------|
| hydrate | `letter_group_instance_authority.py` / FE `authorityRowsFromFinishSetup` | legacy → instances once |
| coalesce / write | BE `coalesce_letter_group_authority_for_finish` on finish-setup save | omit-preserve; mint UUID; project |
| projection | `project_instances_to_legacy_finishes` / FE `projectInstanceToLegacyFinish` | one-way |
| quantity | `build_volumetric_letters_commercial_quantities` | CPP measurement path |
| placement | `ensure_placements` / FE `ensurePlacementsForInstances` | acm_panel \| none (+ persisted kinds) |

### Legacy consumers (projection kept for)

- Existing Review/Confirm finish cards reading `letter_group_finishes`
- Aggregate / PD opaque finish blob readers
- Any path still calling `letterGroupFinishesFromPayload`

### Retirement checkpoint (Build 2)

Stop writing `letter_group_finishes` once all confirmed consumers read instances; gate with consumer inventory + E2E.

## Files changed (feature)

- `backend/services/letter_group_instance_authority.py` (new)
- `backend/schemas/intake_v4.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/services/letters_commercial_measurement_service.py`
- `backend/tests/test_letter_group_instance_authority_v1.py` (new)
- `frontend/src/lib/intakeV6/letterGroupInstanceAuthority.ts` (new)
- `frontend/src/lib/intakeV6/letterGroupInstanceAuthority.test.ts` (new)
- `frontend/src/lib/intakeV6/intakeV4LetterGroups.ts` (confirmed + backing_mode survive fill drift)
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` (~+1 net; helper wiring only)

## Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_letter_group_instance_authority_v1.py tests/test_letters_commercial_measurement_contract.py tests/test_letters_cpp_measurement_consumption.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/letterGroupInstanceAuthority.test.ts

cd backend
.\.venv\Scripts\python.exe ..\docs\audits\_evidence\2026-07-20_volumetric-letters-authority-instance-placement\runtime_proof.py
```

## Runtime proof fixtures

| Workspace | Role | Result |
|-----------|------|--------|
| `IV6-195E885C` | gradi-curat 4-group (local stand-in for BB8EE3F8) | 4 stable UUIDs; reload/omit OK |
| `IV6-DB2F86B7` | letters + ACM control | hydrate + placement → acm_panel |
| `IV6-13D39D32` | measured ACM QA | letter hydrate only; ACM instance id preserved; no finish PUT |

Evidence: `docs/audits/_evidence/2026-07-20_volumetric-letters-authority-instance-placement/`

## Split/merge ambiguity (documented, not coded around)

| Case | Rule |
|------|------|
| Same `group_key` | Keep `instance_id` |
| New `group_key` | Mint new UUID |
| Confirmed key leaves analysis | Keep orphan instance |
| One key → two new keys | Two new UUIDs + confirmed orphan of old key |
| Two keys → one surviving key | Survivor UUID kept; other confirmed orphan kept |

No array index. No hash-in-ID.

## Build 2 handoff

Operator UI closure · composition proof AcmPanel+Letters · retire legacy projection · optional per-group LED qty UI · diagnostics page.
