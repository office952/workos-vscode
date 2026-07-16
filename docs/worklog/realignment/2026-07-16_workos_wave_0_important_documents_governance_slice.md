# WorkOS Wave 0 — Documente importante (Governance slice)

**Date:** 2026-07-16  
**Scope:** Minimal visible slice — read-only section in `/governance` → tab `truth` (Surse de adevăr).  
**Out of scope:** W0-B6 Documentation Center, new routes, CMS, upload/edit, `/modules` duplication.

## What shipped

- `ImportantDocumentsSection` consumes B2 `GET /api/v1/system/documentation` via existing page fetch (`docsResult`).
- Detail open uses `GET .../documentation/{document_id}?include_content=true` only (no arbitrary path).
- States: loading, list, empty, forbidden, unavailable; attention flags for STALE / SUPERSEDED / OWNER_REVIEW.
- No claim that index membership = canonical authority.

## Files

- `frontend/src/components/workos/ImportantDocumentsSection.tsx`
- `frontend/src/api/documentationIndex.ts` (detail client + attention helper)
- `frontend/src/pages/Governance.tsx` (wire into `TruthHierarchyView`)
- Tests: `Governance.test.tsx`, `ImportantDocumentsSection.test.tsx`, `documentationIndex.test.ts`

## Acceptance

1. Visible under Governance Surse de adevăr  
2. List from B2, not a separate hardcoded corpus  
3. Status + authority visible  
4. Stale / superseded marked  
5. Read-only open  
6. Allowlisted index only  
7. Not a Documentation Center  
