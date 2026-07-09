# RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1

## Verdict

```text
RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_READY
```

## Scope

Docs-only / contract-only slice for valid source semantics of:

```text
components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m
```

Allowed:

- architecture contract doc;
- QA note;
- worklog.

Forbidden in this slice:

- no runtime writer
- no Product Truth writes
- no UI changes
- no Pricing changes
- no adapter changes
- no runtime DB changes
- no seed run
- no Quote / Order / Execution
- no ProductAggregate / TaskGraph / ExecutionPlan
- no DB migration

## Safety gate

- HEAD confirmed: `f3d1a88`
- no staged files before work
- `git diff --check` clean before work
- unrelated dirty untracked worktree preserved untouched

## Audit summary

Current perimeter-like signals found in code:

1. `quote_geometry.letter_perimeter_m` and `geometry_source` are populated from analyzer/path geometry flows.
2. `return_material_perimeter_ml` exists in generic Product Truth draft geometry, but not as canonical `return_cant` confirmed truth.
3. readonly mapper classifies `quote_geometry.letter_perimeter_m` as `context_only` and blocked.
4. readonly adapter emits `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` and geometry-context warnings.
5. Review/UI surfaces compute operator perimeter displays, but those are display/diagnostic values only.
6. backend geometry services derive path perimeters from analyzer/path summaries, but do not write canonical confirmed return-cant perimeter truth.

Key finding:

```text
there is no existing owner-safe canonical source today for components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m
```

That absence is a contract gap, not a reason to leave the contract undefined.

## Decision summary

Canonical geometry shape should be:

```text
geometry = {
  perimeter_source: "missing" | "evidence_only" | "operator_confirmed" | "imported_verified_truth" | "system_migration_verified",
  evidence_perimeter_m?: number,
  confirmed_perimeter_m?: number,
  confirmed_perimeter_source?: "operator_confirmed" | "imported_verified_truth" | "system_migration_verified",
  confirmed_perimeter_at?: string,
  confirmed_by?: string,
  blockers: string[]
}
```

Accepted confirmed sources:

- explicit operator confirmation
- imported verified truth with provenance
- system migration verified with audit/provenance

Forbidden confirmed sources:

- raw analyzer output
- raw `quote_geometry.letter_perimeter_m`
- layer geometry evidence
- Step 1 confirmed
- layer role selected
- `finish_setup.confirmed`
- row confirmed
- pricing keys present
- product composition confirmed

## Required rules

1. `quote_geometry.letter_perimeter_m` may populate only `evidence_perimeter_m`.
2. When quote geometry is the source, `perimeter_source` must be `evidence_only`.
3. Quote geometry cannot populate `confirmed_perimeter_m`.
4. Quote geometry cannot set component `confirmation_state = confirmed`.
5. `confirmed_perimeter_m` must be finite, positive, in meters, tied to stable `instance_key`, and tied to valid `layer_group_ids` / `source_ref`.
6. `confirmed_perimeter_m` cannot be copied from evidence without explicit confirmation action or verified provenance.
7. If `evidence_perimeter_m` and `confirmed_perimeter_m` diverge beyond the approved tolerance, blocker `RETURN_CANT_PERIMETER_EVIDENCE_CONFLICT` is required.

## Canonical blockers

- `RETURN_CANT_CONFIRMED_PERIMETER_MISSING`
- `RETURN_CANT_PERIMETER_EVIDENCE_ONLY`
- `RETURN_CANT_PERIMETER_CONFIRMATION_MISSING`
- `RETURN_CANT_PERIMETER_SOURCE_INVALID`
- `RETURN_CANT_PERIMETER_UNIT_INVALID`
- `RETURN_CANT_PERIMETER_NON_POSITIVE`
- `RETURN_CANT_PERIMETER_INSTANCE_MISMATCH`
- `RETURN_CANT_PERIMETER_LAYER_MAPPING_MISSING`
- `RETURN_CANT_PERIMETER_EVIDENCE_CONFLICT`

## Relationship with component confirmation

1. No `confirmed` component truth if `confirmed_perimeter_m` is missing.
2. `evidence_only` geometry remains blocked with `RETURN_CANT_PERIMETER_EVIDENCE_ONLY`.
3. `confirmed_perimeter_m` without component confirmation stays `draft` or `blocked`, not `confirmed`.
4. Component confirmation without `confirmed_perimeter_m` stays blocked.

## Source matrix summary

- `quote_geometry.letter_perimeter_m`, analyzer perimeter, and layer geometry evidence can populate evidence only.
- manually confirmed operator perimeter, imported verified truth, and system migration verified can populate confirmed perimeter, but only with provenance and valid instance/layer mapping.
- workflow confirmations and selection signals cannot populate either evidence or confirmed perimeter truth by themselves.

## Next-slice decision

The perimeter source contract is ready, but layer/source mapping remains insufficient for writer planning.

Recommended next prompt:

```text
RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1
```

## Files created

- `docs/architecture/product-system/RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT.md`
- `docs/qa/return-cant-confirmed-perimeter-source-contract-2026-07-09/RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_confirmed_perimeter_source_contract_v1.md`

## Validation

- docs-only diff
- `git diff --check`
- no tests required
- no build required