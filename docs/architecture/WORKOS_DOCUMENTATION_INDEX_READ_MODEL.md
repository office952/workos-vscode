# WorkOS Documentation Index Read Model

> **W0-B2** · `GO_W0_B2_DOCUMENTATION_INDEX_READ_MODEL` · Date: 2026-07-16  
> **Read-only** · **No Documentation Center UI** · **No menu changes**  
> Index version: `workos_documentation_index/v1`  
> Reuses: `workos_truth_metadata/v1` (`DocumentReference`, visibility, drift)

---

## Architecture: Hybrid (Option C)

| Option | Verdict |
|--------|---------|
| A Static-only hand list | Rejected alone — hard to keep file existence in sync |
| B Directory scan alone | Rejected — directory ≠ authority |
| **C Hybrid** | **Chosen** — explicit registry entries + allowlist prefixes + on-disk verification |

**Metadata precedence:** controlled registry fields win. Filename/directory never assign `CANONICAL_CURRENT`. Filesystem mtime ≠ validity.

---

## Components

| Piece | Path |
|-------|------|
| Registry | `backend/config/document_index_registry.json` |
| Service | `backend/services/documentation_index_service.py` |
| Schemas | `backend/schemas/documentation_index.py` |
| API | `GET /api/v1/system/documentation` · `GET /api/v1/system/documentation/{document_id}` |
| Permission | `system.documentation_read` (admin only) |
| Tests | `backend/tests/test_documentation_index.py` |

---

## Security

- Allowlisted prefixes + exact paths only  
- Path normalization + resolve under repo root  
- Reject `..`, absolute, UNC, encoded traversal  
- Lookup by `document_id` only — never arbitrary path query  
- Visibility: API withholds `OWNER_ONLY`, `RESTRICTED`, `HIDDEN_FROM_UI`  
- Optional Markdown body: UTF-8, size-capped, no write  

---

## Binding rules

1. Git remains canonical store of documents.  
2. Index is projection metadata.  
3. No automatic canonical promotion.  
4. Runtime/health does not define architecture.  
5. Display labels (`display_label_ro`) never replace `document_id` / technical IDs.  
6. Routes, enums, API field names, Figma IDs unchanged in this build.

---

## Owner verification (no UI page)

1. Start backend (`npm run dev:backend` or uvicorn).  
2. As **admin**, `GET /api/v1/system/documentation` → 200 + list.  
3. `GET /api/v1/system/documentation/workos-truth-metadata-contract` → detail.  
4. As **viewer** → 403.  
5. Path-like id → 400/404.  

Or without HTTP: `DocumentationIndexService().list_documents()` in Python.

**Intentionally not visible:** Documentation Center page, menu entries, operator UI labels.
