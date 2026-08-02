# 2026-08-02 — F7A.1 Pre-materialization truth gap closure

## Status

```text
F7A.1 = PASS
WC registry fidelity = PASS (WC_CNC_ROUTING canonical)
Premount hard ban = PASS (DEC-002=A)
Fixture DAG = PASS
POST materialize = NOT EXECUTED
DEC-009 recommendation = B (await Owner written GO)
F7B = NOT STARTED
```

## Changes

- `data/operational_workcenters.py` — canonical / non-canonical WC codes
- catalogs BOM-only + activation helper (always false today)
- Aggregate / bridge / EP identity / preview enforce premount ban + WC registry warnings
- F7A fixture WC aligned to registry
- Architecture docs 08 / 21 resynced for recorded DECs

## Tests

123 targeted backend passed; s56 tip preexisting fail reported.
