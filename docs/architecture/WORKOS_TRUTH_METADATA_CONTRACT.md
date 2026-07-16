# WorkOS Truth Metadata Contract

> **Technical contract (W0-B1)** · `metadata_version`: `workos_truth_metadata/v1`  
> **NOT a parallel source of truth** · Canonical documentation remains in Git  
> Executable schemas: `backend/schemas/truth_metadata/`  
> Tests: `backend/tests/test_truth_metadata_contract.py`  
> Fixtures: `backend/tests/fixtures/truth_metadata/` (`TEST_FIXTURE` / `NOT_CANONICAL_TRUTH`)

## Purpose

Shared read-only projection metadata for future:

- Harta sistemelor
- Guvernanța sistemului
- Centrul de documentație
- Page DoD / Documentation Impact Gate / drift detection

## Principles

1. Git remains canonical for architecture documents.
2. UI must not write architectural claims (no write API in W0-B1).
3. Runtime evidence confirms behavior; it does **not** prove approved architecture.
4. Claims require authority, source, owner (when canonical), status, validation, evidence, supersession where relevant.
5. Romanian display fields are separated from technical identifiers.

## Models

| Model | Module |
|-------|--------|
| `TruthClaim` | `schemas/truth_metadata/claim.py` |
| `AuthorityReference`, `EvidenceReference`, `FigmaReference`, `DisplayMetadata` | `references.py` |
| `DocumentReference`, `SystemNode`, `PageNode`, `TypedEdge`, `DriftRecord` | `entities.py` |
| Enums | `enums.py` |

## Storage

**Option B:** typed Pydantic schemas + non-canonical test fixtures only.  
No DB migration. No production claim registry. No Documentation Center API.

## Binding constants

- `TRUTH_METADATA_VERSION = "workos_truth_metadata/v1"`
- Runtime evidence `authority_rank` ≤ 49
- Canonical authority types require owner on `CURRENT` / `CURRENT_WITH_GUARDS`
- Figma `FIGMA_APPROVED` authority requires `APPROVED` or `APPROVED_WITH_NOTES`

## Plan reference

`docs/plans/2026-07-16-workos-wave-0-foundation-truth-pages-plan.md` (W0-B1)
