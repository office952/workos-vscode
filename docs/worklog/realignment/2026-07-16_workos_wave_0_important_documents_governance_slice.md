# WorkOS Wave 0 — Documente importante (Governance slice)

**Owner authorization:** GO — COMMIT IMPORTANT DOCUMENTS GOVERNANCE SLICE  
**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD before finalization:** `3e2fc87afb589b4c9fb3990bb22e4ad5b7b4cda6`  
**Implementation commit (already on branch):** `eff40a90e523fb1bff0261baa7699eefc4ddfc22`  
**Message:** `feat(wave0): show important documents in governance`

## Objective

Finalize and verify the existing read-only **Documente importante** section in `/governance` → tab technical ID `truth` (visible: Surse de adevăr). No new functionality. No W0-B6.

## Files (implementation — already committed in `eff40a9`)

| File | Role |
|------|------|
| `frontend/src/components/workos/ImportantDocumentsSection.tsx` | Read-only section UI + reader modal |
| `frontend/src/components/workos/ImportantDocumentsSection.test.tsx` | State coverage |
| `frontend/src/api/documentationIndex.ts` | B2 list + detail (`document_id`) + attention helper |
| `frontend/src/api/documentationIndex.test.ts` | List/detail/error/attention tests |
| `frontend/src/pages/Governance.tsx` | Wire into `TruthHierarchyView` only |
| `frontend/src/pages/Governance.test.tsx` | Truth-tab section coverage |

## Data source

- List: `GET /api/v1/system/documentation` (W0-B2 allowlisted index)
- Detail: `GET /api/v1/system/documentation/{document_id}?include_content=true`
- Permission: `system.documentation_read` (unchanged)
- No second registry; no hardcoded corpus; no arbitrary path input

## Security / read-only boundary

- GET only (no POST/PUT/PATCH/DELETE)
- No edit / upload / delete / approve / canonical mutation controls
- Open by `document_id` only
- Footer: „Fără editare · fără upload · lookup doar după document_id”
- Index membership ≠ canonical authority (explicit copy)

## States

| State | Covered |
|-------|---------|
| loading (`docsResult === null`) | YES (component + tests) |
| populated list | YES (runtime: 11 items) |
| empty | YES (tests) |
| permission denied | YES (tests + UI) |
| API unavailable | YES (tests + UI) |
| detail loading / error | YES (component) |
| STALE / SUPERSEDED markers | YES (unit + Governance tests; not present in live registry today) |
| OWNER REVIEW REQUIRED | YES (runtime: `workos-canonical-documentation-authority-policy`) |

## Tests (re-run 2026-07-17)

```text
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/Governance.test.tsx src/api/documentationIndex.test.ts src/components/workos/ImportantDocumentsSection.test.tsx
```

**Result:** 3 files, **19 passed**, 0 failed · ~2.18s  
**Warnings:** React `act(...)` noise from async `fetchDocumentationIndex` in Governance tests (non-blocking).

## Frontend build

```text
cd frontend
npx --yes pnpm@8.10.0 run build
```

**Result:** PASS (`vite build`, ~18s)  
**Warnings:** preexisting CSS minify / chunk-size / browserslist (unrelated to slice). No type/bundle errors from this slice.

## Runtime verification

- URL: `http://127.0.0.1:3000/governance`
- FE `:3000` + BE `:8001` (canonical local API base)
- Path: Sistem → Guvernanța sistemului → tab Surse de adevăr → Documente importante
- Observed: 11 allowlisted docs from `workos_documentation_index/v1`
- Opened: `workos-canonical-documentation-authority-policy` (read-only modal; footer confirms no edit/upload; lookup by document_id)
- Attention: `OWNER_REVIEW_REQUIRED` visible on that document
- Live registry had no STALE/SUPERSEDED entries at verification time (markers proven in tests)

## Screenshots

Folder: `docs/qa/workos-wave0-important-documents-governance-slice/screenshots/`

| File | Content |
|------|---------|
| `01_governance_truth_important_docs_list.png` | Documente importante list |
| `02_important_docs_owner_review_and_reader.png` | Read-only reader + OWNER_REVIEW context |
| `03_governance_tab_surse_de_adevar_selected.png` | Tab Surse de adevăr selected |
| `04_important_docs_owner_review_marker.png` | OWNER_REVIEW markers on list cards (captured in session; see index if present) |

## Documentation impact

```text
PAGE_MAP_UPDATE
+
GOVERNANCE_UPDATE
+
TRUTH_METADATA_UPDATE
+
WORKLOG_ONLY
```

No claim that W0-B6 / Documentation Center / Governance FINAL is complete.

## Overengineering check

1. Only required visible section? YES  
2. New framework? NO  
3. Second document index? NO  
4. Broad search? NO  
5. Rich Markdown tooling? NO (`<pre>` only)  
6. Unrelated Governance areas changed? NO (truth tab wire only)  
7. Removable without losing visible result? No unnecessary code found

## Forbidden scope confirmation

No W0-B6 · no Documentation Center · no edit/upload · no route/tab/permission renames · no DB · no Module Chain changes · no new menu item.

## Remaining gaps

- No full Documentation Center
- No W0-B6
- Not all Governance tabs made canonical
- Important documents corpus remains allowlisted and limited
- Live STALE/SUPERSEDED fixtures not currently in B2 registry (test-covered)

## Next safe step

Owner visually reviews `/governance` → Surse de adevăr → Documente importante.  
Continue only after a separate owner decision. Do not start W0-B6.

## Finalization commit

Staged only worklog + QA evidence for this slice (implementation already at `eff40a9`).  
See git log for hash after finalization commit.
