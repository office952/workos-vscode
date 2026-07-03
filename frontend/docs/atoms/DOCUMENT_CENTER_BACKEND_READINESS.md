# Document Center — Backend Readiness

**Generated**: 2026-06-03  
**Status**: 🔴 NOT WIRED — No backend entity exists

---

## Current State

### Backend (DOES NOT EXIST ❌)

- No `documents` data model in `data_models/`
- No `documents` router in `routers/`
- No `documents` service in `services/`
- No `documents` table in database

### Frontend (DEMO ONLY)

- `DocumentCenter.tsx` contains hardcoded `mockDocuments` array
- Documents are generated from existing quotes/orders data at render time
- All actions (Vezi, Descarcă, Trimite, Semnat, Detalii) are disabled with reasons
- KPI cards show counts from mock data
- Detail drawer shows metadata but no real persistence
- Document lifecycle panel is UI-only

---

## Proposed Entity: `documents`

### Schema

```json
{
  "title": "documents",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "description": "Primary key, auto-increment"
    },
    "code": {
      "type": "string",
      "description": "Business code like DOC-0001"
    },
    "document_type": {
      "type": "string",
      "description": "oferta_pdf | contract | factura_proforma | factura_finala | aviz_livrare | proces_verbal | garantie | bon_constatare"
    },
    "version": {
      "type": "integer",
      "description": "Document version number, starts at 1"
    },
    "status": {
      "type": "string",
      "description": "draft | generat | de_trimis | trimis | vizualizat | semnat | acceptat | expirat | arhivat"
    },
    "client_id": {
      "type": "integer",
      "description": "FK clients.id"
    },
    "client_name": {
      "type": "string",
      "description": "Denormalized client name"
    },
    "linked_entity_type": {
      "type": "string",
      "description": "quote | order | contract | null"
    },
    "linked_entity_id": {
      "type": "integer",
      "description": "FK to linked entity"
    },
    "linked_entity_code": {
      "type": "string",
      "description": "Denormalized entity code (e.g., OFR-2201)"
    },
    "title": {
      "type": "string",
      "description": "Document title/name"
    },
    "file_url": {
      "type": "string",
      "description": "Storage URL for generated/uploaded file"
    },
    "file_size_bytes": {
      "type": "integer",
      "description": "File size"
    },
    "mime_type": {
      "type": "string",
      "description": "application/pdf, image/png, etc."
    },
    "generated_at": {
      "type": "string",
      "description": "ISO datetime when document was generated"
    },
    "sent_at": {
      "type": "string",
      "description": "ISO datetime when sent to client"
    },
    "viewed_at": {
      "type": "string",
      "description": "ISO datetime when client viewed"
    },
    "signed_at": {
      "type": "string",
      "description": "ISO datetime when signed/accepted"
    },
    "expires_at": {
      "type": "string",
      "description": "ISO datetime for document expiry"
    },
    "responsible": {
      "type": "string",
      "description": "Person responsible for this document"
    },
    "notes": {
      "type": "string",
      "description": "Internal notes"
    },
    "created_at": {
      "type": "string",
      "description": "ISO datetime"
    },
    "updated_at": {
      "type": "string",
      "description": "ISO datetime"
    }
  }
}
```

---

## Proposed Endpoints

```
GET    /api/v1/entities/documents              → list with filters (client, type, status, linked_entity)
GET    /api/v1/entities/documents/{id}         → single document detail
POST   /api/v1/entities/documents              → create document record
PUT    /api/v1/entities/documents/{id}         → update metadata/status
DELETE /api/v1/entities/documents/{id}         → soft delete / archive

POST   /api/v1/documents/generate              → generate document from template
POST   /api/v1/documents/{id}/upload           → upload signed/external document
POST   /api/v1/documents/{id}/send             → mark as sent (update sent_at)
POST   /api/v1/documents/{id}/mark-signed      → mark as signed (update signed_at)
POST   /api/v1/documents/{id}/regenerate       → create new version
GET    /api/v1/documents/{id}/history          → version history
GET    /api/v1/documents/lifecycle/{order_id}  → document lifecycle for an order
```

---

## Document Lifecycle (per Order)

A complete order should generate documents in this sequence:

1. **Ofertă PDF** — generated from quote, sent to client
2. **Contract** — generated after quote acceptance
3. **Factură proformă** — generated for prepayment
4. **Aviz de livrare** — generated at delivery
5. **Proces verbal** — generated at handover
6. **Factură finală** — generated after completion
7. **Garanție** — generated post-delivery
8. **Bon constatare** — generated for service/repair

---

## Actions Matrix

| Action | Backend Endpoint | Status |
|--------|-----------------|--------|
| Vezi (View) | `GET /documents/{id}` + `file_url` | Needs backend |
| Descarcă (Download) | `file_url` direct download | Needs storage |
| Trimite (Send) | `POST /documents/{id}/send` | Needs backend |
| Marchează trimis | `POST /documents/{id}/send` | Needs backend |
| Marchează semnat | `POST /documents/{id}/mark-signed` | Needs backend |
| Încarcă semnat | `POST /documents/{id}/upload` | Needs backend + storage |
| Regenerare | `POST /documents/{id}/regenerate` | Needs backend |
| Arhivează | `PUT /documents/{id}` status=arhivat | Needs backend |

---

## Implementation Notes

- File storage should use existing `storage` service (`routers/storage.py` exists)
- PDF generation can leverage existing `quote_pdf_service.py` patterns
- Document templates should be configurable (not hardcoded)
- Version history tracks all regenerations with diff metadata
- Cross-links to Client Workspace, Quotes, Orders via `linked_entity_type` + `linked_entity_id`