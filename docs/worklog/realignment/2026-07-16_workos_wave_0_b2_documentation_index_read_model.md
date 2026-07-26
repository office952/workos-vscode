# Worklog — W0-B2 Documentation Index Read Model

**Date:** 2026-07-16  
**Build ID:** W0-B2  
**GO:** `GO_W0_B2_DOCUMENTATION_INDEX_READ_MODEL`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD before:** `47410c4`  
**HEAD after:** *(set after commit)*

---

## Objective

Safe read-only Hybrid documentation index + metadata read model; no Documentation Center UI; no menu; no technical renames.

## Research

- System router patterns (`/api/v1/system/*`), `require_permission`, auto router discovery  
- W0-B1 `DocumentReference` / path normalize  
- Permission matrix → added `system.documentation_read` (admin)

## Architecture choice

**Hybrid (C):** explicit registry + allowlist prefixes/exact paths + on-disk verification.  
Rejected A (manual-only) and B (scan-only / directory≠authority).

## Corpus

Controlled entries in `backend/config/document_index_registry.json` (Wave 0 plans/contracts, terminology, product/commercial/EP boundaries, AGENTS.md, index doc itself).

## Security / visibility / path safety

Allowlist + normalize + resolve under repo root; reject traversal/absolute/UNC/encoded `..`.  
API withholds OWNER_ONLY / RESTRICTED / HIDDEN_FROM_UI.  
Lookup by `document_id` only.

## Terminology safety

OD-TERM-01…11 recorded as APPROVED display direction in registry.  
UI strings **not** changed. Technical IDs/routes unchanged.  
Tests assert `technical_id == document_id` ≠ display label.

## Tests

```text
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_documentation_index.py -q
# 15 passed
```

## API verdict

GET-only:
- `GET /api/v1/system/documentation`
- `GET /api/v1/system/documentation/{document_id}`  
Permission: `system.documentation_read` (admin). Optional `include_content` for Markdown.

## Documentation impact

`CONTRACT_DOC_UPDATE` + `TRUTH_METADATA_UPDATE` + `TERMINOLOGY_UPDATE` + `WORKLOG_ONLY`  
Truth-page impact: infrastructure only — Harta/Guvernanță/Centru UI not built.

## Files

- `backend/config/document_index_registry.json`
- `backend/services/documentation_index_service.py`
- `backend/schemas/documentation_index.py`
- `backend/routers/documentation_index.py`
- `backend/dependencies/permissions.py` (additive permission)
- `backend/tests/test_documentation_index.py`
- `docs/architecture/WORKOS_DOCUMENTATION_INDEX_READ_MODEL.md`
- terminology registry OD-TERM recording
- Wave 0 plan status
- this worklog

## Forbidden scope

No FE/nav/ModuleChain/Governance UI · no Figma · no DB migration · no B4–B8 · no technical rename · no auto-canonical promotion

## Next step

Owner reviews B2 → separate GO for **W0-B4 and/or W0-B5** honesty baseline.  
Do not start B4/B5 automatically.
