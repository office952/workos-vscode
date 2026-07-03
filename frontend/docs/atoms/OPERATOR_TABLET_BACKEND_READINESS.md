# Operator Tablet Mode — Backend Readiness

**Generated**: 2026-06-03  
**Status**: ⚠️ PARTIAL — Backend API exists, frontend uses demo data

---

## Current State

### Backend (EXISTS ✅)

The backend has a full operator tasks router at `/api/v1/operator`:

```
Router: routers/operator_tasks.py
Prefix: /api/v1/operator
Tags:   ["operator"]
Auth:   Requires authenticated user

Endpoints:
  GET  /api/v1/operator/tasks          → all tasks from execution plans, enriched
  POST /api/v1/operator/task-action    → start/pause/complete/block/resume/unblock
```

#### GET /api/v1/operator/tasks — Response

Returns all tasks from all execution plans, enriched with order info and reality status:

```json
{
  "tasks": [
    {
      "task_id": "uuid",
      "order_id": 123,
      "order_code": "ORD-1120",
      "name": "Printare latex",
      "process_type": "print_latex",
      "machine_type": "printer_latex",
      "estimated_time_minutes": 45,
      "quantity": 2,
      "layer_id": "layer-1",
      "status": "assigned|in_progress|done|blocked|paused",
      "started_at": "ISO datetime or null",
      "ended_at": "ISO datetime or null",
      "blocked_at": "ISO datetime or null",
      "paused_at": "ISO datetime or null",
      "actual_minutes": "number or null",
      "client": "Client Name",
      "product": "Product description",
      "order_status": "in_execution"
    }
  ],
  "total": 15
}
```

#### POST /api/v1/operator/task-action — Request/Response

```json
// Request
{
  "order_id": 123,
  "task_id": "task-uuid",
  "action": "start|pause|complete|block|resume|unblock",
  "operator_name": "optional",
  "reason": "optional (for block action)"
}

// Response
{
  "status": "ok",
  "action": "start",
  "task_id": "task-uuid",
  "timestamp": "2026-06-03T10:30:00+00:00"
}
```

**Action validations** (backend enforces):
- `start`: Creates reality entry if not exists
- `pause`: Requires task started, not ended, not already paused/blocked
- `complete`: Requires task not blocked, not paused
- `block`: Requires task started, not ended, not already blocked
- `resume`: Requires task actively paused
- `unblock`: Requires task actively blocked

---

### Frontend (DEMO ❌)

- `TabletMode.tsx` uses `generateDemoTasks()` function for static task data
- `workstationRouting.ts` provides station configuration (valid as frontend config)
- Task actions (Start/Block/Finalize) are demo buttons with no API calls
- Help Request modal is UI-only (no persistence)

---

## Recommendation

### Phase 1: Wire Task Queue (P1)

1. Create `src/api/operatorTasks.ts`:
   ```typescript
   import { getAPIBaseURL } from '../lib/config';
   
   const base = () => `${getAPIBaseURL()}/api/v1/operator`;
   
   export interface OperatorTask {
     task_id: string;
     order_id: number;
     order_code: string;
     name: string;
     process_type: string;
     machine_type: string;
     estimated_time_minutes: number;
     quantity: number;
     status: 'assigned' | 'in_progress' | 'done' | 'blocked' | 'paused';
     started_at: string | null;
     ended_at: string | null;
     blocked_at: string | null;
     paused_at: string | null;
     actual_minutes: number | null;
     client: string;
     product: string;
   }
   
   export async function listOperatorTasks(): Promise<{ tasks: OperatorTask[]; total: number }> { ... }
   export async function performTaskAction(req: TaskActionRequest): Promise<TaskActionResponse> { ... }
   ```

2. Wire `/tablet/:stationId` to filter tasks by `process_type` matching station's operations

3. Wire task action buttons to `POST /api/v1/operator/task-action`

4. Keep `workstationRouting.ts` as station configuration (maps stations → operations → skills)

5. Demo tasks become fallback only when API returns empty or errors

### Phase 2: Enhanced Tablet Features (P2)

| Feature | Status | Backend Needed |
|---------|--------|---------------|
| Start task | ✅ Backend exists | Wire to `task-action` with `action: "start"` |
| Block task | ✅ Backend exists | Wire to `task-action` with `action: "block"` |
| Finalize task | ✅ Backend exists | Wire to `task-action` with `action: "complete"` |
| Pause task | ✅ Backend exists | Wire to `task-action` with `action: "pause"` |
| Resume task | ✅ Backend exists | Wire to `task-action` with `action: "resume"` |
| Unblock task | ✅ Backend exists | Wire to `task-action` with `action: "unblock"` |
| Help request | ❌ No backend | New endpoint needed: `POST /api/v1/operator/help-request` |
| Timing tracking | ✅ Backend calculates | `actual_minutes` derived from start/end timestamps |
| Points/rewards | ❌ No backend | Future: link completed tasks to reward points |

---

## workstationRouting.ts — Remains Valid

The frontend routing configuration maps:
- Station ID → Station name, operations, required skills
- Operation type → Machine type, estimated time
- Station → Operator assignments

This is **correctly frontend-only** — it's routing/display config, not task data.
Task data (what work is queued) comes from backend execution plans.

---

## Future Endpoints Needed

```
POST /api/v1/operator/help-request          → create help request
GET  /api/v1/operator/help-requests         → list active help requests
PUT  /api/v1/operator/help-requests/{id}    → resolve/take help request
GET  /api/v1/operator/tasks/mine            → tasks for current operator (exists in router but needs auth context)
GET  /api/v1/operator/station-summary       → KPIs per station (tasks done, avg time, etc.)
```