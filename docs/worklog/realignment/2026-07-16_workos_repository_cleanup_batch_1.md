# Worklog — Repository cleanup batch 1 + B2 document sources

**Date:** 2026-07-16  
**Owner GO:** Deciziile 1, 4, 5, 6, 8, 16 (only)  
**Repository:** `C:/w/psiso`  
**Remote:** `https://github.com/office952/workos-vscode.git`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD before cleanup:** `eff40a90e523fb1bff0261baa7699eefc4ddfc22`

## Approved decisions executed

| Decision | Action |
|----------|--------|
| 1 | STERGEM `_export_*` + readiness manifest + gitignore |
| 4 | STERGEM `_review_*`, empty `backend/scripts/package.json`, `figma-pd02.js` |
| 5 | STERGEM closed CE `windows-ghost-listener-8000-clear-v1/` |
| 6 | STERGEM `database_candidates/` (not committed) + gitignore |
| 8 | COMITEM SEPARAT five B2 architecture sources |
| 16 | STERGEM `_activate_postjob_proof_material.py` |

Deferred (untouched): 2, 3, 7, 9, 10, 11, 12, 13, 14, 15.

## Files deleted

- `_review_463707b.diff`
- `_review_letter_group_old.tsx`
- `backend/scripts/package.json`
- `.compound-engineering/product-definition-ui-ux-v1/figma-pd02.js` (+ empty parent dir)
- `.compound-engineering/windows-ghost-listener-8000-clear-v1/` (10 files)
- `database_candidates/` (`README.txt`, `EXCLUDED_DB_FILES.txt` — path inventory only)
- `backend/scripts/_activate_postjob_proof_material.py`
- `_export_workos_systems_readiness_audit_2026-07-08/` (64 files; source retained under `docs/qa/workos-systems-readiness-audit-2026-07-08/`)
- `workos_systems_readiness_audit_2026-07-08_MANIFEST.md`

## Blocked deletions

None for approved targets. Historical mentions of deleted paths remain in CE isolation research / deferred root `WORKOS_*` notes (intentional; not required evidence).

## `.gitignore` rules added (root-only)

| Rule | Blocks | Safe because | Does not hide |
|------|--------|--------------|---------------|
| `/_review_*` | Root review leftovers | Leading `/` = repo root only | Files under `docs/` / `frontend/` with “review” in name |
| `/_export_*/` | Root export handoff packs | Sources live in `docs/qa/` | `docs/export/` |
| `/workos_systems_readiness_audit_*_MANIFEST.md` | Root readiness manifests | Pair of `_export_*` packs | Other manifests under `docs/` |
| `/database_candidates/` | Local DB path inventory | Machine-specific | Application source |

## References fixed

Minimal wording updates (historical export docs no longer point at live `database_candidates/`):

- `ENVIRONMENT_NOTES.md`
- `EXPORT_MANIFEST.md`
- `INSTALL_LOCAL.md`
- `README_EXPORT.md`

## Cleanup commit

- Message: `chore(repo): remove local and reproducible artifacts`
- Hash: `9038209e74cab8abe2ca2ef5c2b9441add195dfa`
- Staged: `.gitignore`, four export-doc link fixes only

## B2 documents committed (Operation B)

| Path | document_id | Registry match |
|------|-------------|----------------|
| `docs/architecture/WORKOS_UI_TERMINOLOGY_OWNER_DECISION_PACK.md` | `workos-ui-terminology-owner-decision-pack` | YES |
| `docs/architecture/WORKOS_CANONICAL_DOCUMENTATION_AUTHORITY_POLICY.md` | `workos-canonical-documentation-authority-policy` | YES |
| `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md` | `product-truth-confirmation-policy` | YES |
| `docs/architecture/product-system/COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md` | `commercial-preview-boundary-contract` | YES |
| `docs/architecture/product-system/PRE_ORDER_EXECUTION_PLAN_PREVIEW_BOUNDARY_CONTRACT.md` | `pre-order-execution-plan-preview-boundary` | YES |

No architecture rewrite; no secrets/local paths found in scan.

## Validation

| Check | Result |
|-------|--------|
| `pytest tests/test_documentation_index.py` | 15 passed |
| Vitest Important Documents (3 files) | 19 passed |
| `vite build` | pass |
| Runtime `/governance` → Surse de adevăr → Documente importante | PASS |
| Opened document_id | `commercial-preview-boundary-contract` (read-only; footer no edit/upload) |

## B2 docs commit

- Message: `docs(wave0): commit allowlisted architecture sources`
- Contents: five B2 architecture paths + this worklog
- Hash: filled after commit

## Remaining dirty tree (high level)

Preserved / deferred: isolation CE+QA, root `WORKOS_*_2026-07-06`, true-e2e review package, worklogs/plans/master, PreOrder prototypes, BE tests, `productDefinitionPreview.ts` composition types, inventory helper CSVs under cleanup QA folder.

## Next safe step

Owner reviews clutter reduction + Governance Important Documents, then chooses next isolated preservation commit or cleanup batch (deferred decisions).
