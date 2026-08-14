# Wave 5 — Documents runtime status

```text
DOCUMENTS_RUNTIME_STATUS = MOCK
DOCUMENTS_ROUTE = /documents → DocumentCenter.tsx
DATA_API = quotes + orders via useBackendData (no /api/v1/documents)
PERSISTENCE_STORE = NONE
UPLOAD_ENDPOINT = NONE
DOWNLOAD_ENDPOINT = NONE
LINKED_CONSUMERS = client-side mock rows point at /quotes and /orders (CTAs often disabled)
DISABLED_CONTROLS = Încarcă, Descarcă, Încarcă semnat, row actions
STATIC_CONTENT = generateMockDocuments(quotes, orders)
```

## Proof

`DocumentCenter` builds `MockDocument[]` in the browser from live quote/order **identity** (id, client, status, dates). It does not load or save a document store. Backend has quote-PDF / documentation-index routers; they are **not** this hub.

Lifecycle chips include `coming_soon` (contract, bun de tipar). The page can look like a registry because it reuses real commercial ids. It is still a mock hub.

Do not create a store. Do not activate uploads.
