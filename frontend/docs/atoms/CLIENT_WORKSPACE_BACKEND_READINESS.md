# Client Workspace — Backend Readiness

**Generated**: 2026-06-03  
**Status**: ⚠️ PARTIAL — Backend entity exists, frontend not directly wired

---

## Current State

### Backend (EXISTS ✅)

The backend has a full `clients` entity router at `/api/v1/entities/clients`:

```
Router: routers/clients.py
Prefix: /api/v1/entities/clients
Tags:   ["clients"]

Endpoints:
  GET    /api/v1/entities/clients          → paginated list (sort, filter)
  GET    /api/v1/entities/clients/all      → all clients (no pagination)
  GET    /api/v1/entities/clients/{id}     → single client by ID
  POST   /api/v1/entities/clients          → create new client
  POST   /api/v1/entities/clients/batch    → batch create
  PUT    /api/v1/entities/clients/{id}     → update client
  PUT    /api/v1/entities/clients/batch    → batch update
  DELETE /api/v1/entities/clients/{id}     → delete client
  DELETE /api/v1/entities/clients/batch    → batch delete
```

**Client Entity Schema** (`data_models/clients.json`):
```json
{
  "id": "integer (PK)",
  "name": "string",
  "identity_type": "temp | fiscal",
  "temp_ref": "string (optional)",
  "cui": "string (optional, fiscal ID)",
  "contact_person": "string",
  "phone": "string",
  "email": "string",
  "address": "string",
  "city": "string",
  "notes": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Frontend (PARTIAL ⚠️)

- `Clients.tsx` derives client list from `useBackendData()` — aggregates unique client names from intakes, quotes, and orders
- `ClientWorkspace.tsx` filters `useBackendData()` results by `client_name` match
- No direct API call to `/api/v1/entities/clients`
- Client entity types exist in `src/lib/api.ts` (`ClientEntity` interface) but are unused in pages

---

## Cross-Links (Working)

| From | To | Mechanism |
|------|-----|-----------|
| Client → Intakes | Filter by `client_name` | `useBackendData().intakes.filter(i => i.client === clientName)` |
| Client → Quotes | Filter by `client_name` | `useBackendData().quotes.filter(q => q.client === clientName)` |
| Client → Orders | Filter by `client_name` | `useBackendData().orders.filter(o => o.client === clientName)` |
| Intake → Intake Detail | Route link | `/intake/${intake.id}` |
| Quote → (view) | Route link | `/quotes` (filtered) |
| Order → Execution | Route link | `/execution/${order.order_id}` |

---

## Recommendation

### Phase 1: Wire to Client API (P1)

1. Create `src/api/clientsAdmin.ts`:
   ```typescript
   import { getAPIBaseURL } from '../lib/config';
   
   const base = () => `${getAPIBaseURL()}/api/v1/entities/clients`;
   
   export async function listClients(): Promise<ClientEntity[]> { ... }
   export async function getClient(id: number): Promise<ClientEntity> { ... }
   export async function createClient(data: Partial<ClientEntity>): Promise<ClientEntity> { ... }
   export async function updateClient(id: number, data: Partial<ClientEntity>): Promise<ClientEntity> { ... }
   ```

2. Update `Clients.tsx` to call `listClients()` directly instead of deriving from other entities

3. Update `ClientWorkspace.tsx` to:
   - Load client by ID (requires route change to `/clients/:clientId`)
   - OR keep name-based routing but query `/api/v1/entities/clients?name=...`

4. Keep cross-links to intakes/quotes/orders via `client_id` FK

### Phase 2: Enhanced Client Features (P2)

- Client documents tab → requires `documents` entity (see Document Center)
- Client invoices tab → requires invoice/billing entity
- Client contracts tab → requires contracts entity
- Client notes/activity → could use existing entity notes field

---

## What Remains Partial

| Feature | Status | Reason |
|---------|--------|--------|
| Client list display | ⚠️ Derived | Should query clients entity directly |
| Client detail/edit | ❌ Not implemented | Backend PUT exists, UI form needed |
| Client create | ❌ Not implemented | Backend POST exists, UI form needed |
| Client documents | ❌ Demo only | No documents entity |
| Client invoices | ❌ Coming soon | No invoice entity |
| Client contracts | ❌ Coming soon | No contracts entity |
| Client activity timeline | ⚠️ Derived | Auto-generated from entity timestamps |