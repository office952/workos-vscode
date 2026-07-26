## Research — Runtime surface map & verification matrix

Task: `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_RUNTIME_CLOSEOUT`

Purpose: Build the exact runtime verification matrix **without changing code or data**.

---

### Evidence anchors (route mounting + auth)

- Backend router mounting + public health/config:
  - `backend/main.py` (`/health`, `/api/config`, router includes)
- Auth dependency:
  - `backend/dependencies/auth.py` (`get_current_user`)
- RBAC/permissions:
  - `backend/dependencies/permissions.py` (`require_permission`, role mapping incl. `user→admin` only in dev)
- Frontend route table:
  - `frontend/src/App.tsx` (react-router)
- Product System UI E2E navigation/screenshot anchors:
  - `frontend/e2e/product-system-readonly-smoke.spec.ts`
  - `frontend/e2e/product-system-ui-shell-navigation-v1.spec.ts`

---

### Authentication contexts used in matrix

- **public**: no `Depends(get_current_user)`
- **authenticated**: `Depends(get_current_user)`
- **permission-gated**: `Depends(require_permission("<permission_key>"))`

---

## Runtime verification matrix

> Columns: surface | method | URL | auth context | input | expected status | expected identity | write risk | runtime data required

### Backend health + version (public)

- **surface**: backend
  - **method**: GET
  - **URL**: `/health`
  - **auth context**: public
  - **input**: none
  - **expected status**: 200
  - **expected identity**: liveness payload
  - **write risk**: none
  - **runtime data required**: none

- **surface**: backend
  - **method**: GET
  - **URL**: `/database/health`
  - **auth context**: public
  - **input**: none
  - **expected status**: 200
  - **expected identity**: db health payload
  - **write risk**: none
  - **runtime data required**: DB reachable

- **surface**: backend
  - **method**: GET
  - **URL**: `/api/v1/system/version`
  - **auth context**: public
  - **input**: none
  - **expected status**: 200
  - **expected identity**: version/release payload
  - **write risk**: none
  - **runtime data required**: optional env/release metadata

- **surface**: backend
  - **method**: GET
  - **URL**: `/api/v1/system/health`
  - **auth context**: public
  - **input**: none
  - **expected status**: 200
  - **expected identity**: system health payload
  - **write risk**: none
  - **runtime data required**: backend up; DB optional depending on implementation

- **surface**: backend
  - **method**: GET
  - **URL**: `/api/config`
  - **auth context**: public
  - **input**: none
  - **expected status**: 200
  - **expected identity**: runtime config payload (api base)
  - **write risk**: none
  - **runtime data required**: none

### Auth identity + permissions (authenticated)

- **surface**: backend
  - **method**: GET
  - **URL**: `/api/v1/auth/me`
  - **auth context**: authenticated
  - **input**: bearer/cookie
  - **expected status**: 200 (or 401)
  - **expected identity**: `UserResponse`
  - **write risk**: none
  - **runtime data required**: auth context present

- **surface**: backend
  - **method**: GET
  - **URL**: `/api/v1/auth/permissions`
  - **auth context**: authenticated
  - **input**: bearer/cookie
  - **expected status**: 200
  - **expected identity**: permissions payload (raw_role/effective_role/permissions)
  - **write risk**: none
  - **runtime data required**: auth context present

### Product System read surfaces (authenticated; identity-boundary enforcement)

- **surface**: backend product-system
  - **method**: GET
  - **URL**: `/api/v1/product-system/template-availability`
  - **auth context**: authenticated
  - **input**: query params
  - **expected status**: 200
  - **expected identity**: availability response
  - **write risk**: none
  - **runtime data required**: templates seeded in DB

- **surface**: backend product-system
  - **method**: GET
  - **URL**: `/api/v1/product-system/aggregate/{template_code}`
  - **auth context**: authenticated
  - **input**: `template_code`, optional `workspace_id`
  - **expected status**: 200 / 404 / 422
  - **expected identity**: `ProductAggregate`
  - **write risk**: none
  - **runtime data required**: template exists; optional workspace exists

- **surface**: backend product-system
  - **method**: GET
  - **URL**: `/api/v1/product-system/product-definition/{template_code}`
  - **auth context**: authenticated
  - **input**: `template_code`, optional `workspace_id`
  - **expected status**: 200 / 404 / 422
  - **expected identity**: `ProductDefinitionPreview`
  - **write risk**: none
  - **runtime data required**: template exists; optional workspace exists

- **surface**: backend product-system
  - **method**: GET
  - **URL**: `/api/v1/product-system/mini-modules/by-template/{template_code}`
  - **auth context**: authenticated
  - **input**: `template_code`
  - **expected status**: 200 / 422
  - **expected identity**: mini-module registry filtered by template
  - **write risk**: none
  - **runtime data required**: none beyond auth + identity rules

### Quote Snapshot V2 (preview read-bridge; freeze write-like)

- **surface**: backend product-system
  - **method**: POST
  - **URL**: `/api/v1/product-system/quote-snapshot-v2/preview/{template_code}`
  - **auth context**: authenticated
  - **input**: optional JSON body
  - **expected status**: 200 / 404 / 422
  - **expected identity**: `QuoteSnapshotV2` (`persist_status="not_persisted"`)
  - **write risk**: none (designed read-only)
  - **runtime data required**: template/inputs sufficient

- **surface**: backend product-system
  - **method**: POST
  - **URL**: `/api/v1/product-system/quote-snapshot-v2/freeze/{template_code}`
  - **auth context**: authenticated
  - **input**: optional JSON body
  - **expected status**: 200 / 404 / 422
  - **expected identity**: `QuoteSnapshotV2` with persist outcome
  - **write risk**: **write** (persists snapshot when allowed)
  - **runtime data required**: DB + required identifiers for freeze path

- **surface**: backend product-system
  - **method**: GET
  - **URL**: `/api/v1/product-system/quote-snapshot-v2/{snapshot_code}`
  - **auth context**: authenticated
  - **input**: `snapshot_code`
  - **expected status**: 200 / 404
  - **expected identity**: persisted `QuoteSnapshotV2`
  - **write risk**: none
  - **runtime data required**: snapshot exists in DB

### Dossier routes (explicit CRUD; operator must not be able to write)

- **surface**: backend entities
  - **method**: GET
  - **URL**: `/api/v1/entities/product-blueprint-dossiers`
  - **auth context**: authenticated
  - **input**: query JSON + paging
  - **expected status**: 200
  - **expected identity**: list response
  - **write risk**: none
  - **runtime data required**: DB

- **surface**: backend entities
  - **method**: POST
  - **URL**: `/api/v1/entities/product-blueprint-dossiers`
  - **auth context**: permission-gated (`dossier.create`)
  - **input**: JSON create payload
  - **expected status**: 201 / 403 / 409 / 422
  - **expected identity**: created dossier
  - **write risk**: **write**
  - **runtime data required**: DB + referenced template exists

- **surface**: backend entities
  - **method**: PUT
  - **URL**: `/api/v1/entities/product-blueprint-dossiers/{id}`
  - **auth context**: permission-gated (`dossier.update`)
  - **input**: JSON partial update
  - **expected status**: 200 / 403 / 404 / 409 / 422
  - **expected identity**: updated dossier
  - **write risk**: **write**
  - **runtime data required**: DB row exists

- **surface**: backend entities
  - **method**: DELETE
  - **URL**: `/api/v1/entities/product-blueprint-dossiers/{id}`
  - **auth context**: permission-gated (`dossier.delete`)
  - **input**: none
  - **expected status**: 200 / 403 / 404 / 409
  - **expected identity**: deletion response
  - **write risk**: **write**
  - **runtime data required**: DB row exists + status policy allows delete

### Orders + ExecutionPlan V2 (write-like)

- **surface**: backend entities
  - **method**: POST
  - **URL**: `/api/v1/entities/orders/from-quote/{quote_id}`
  - **auth context**: permission-gated (`order.create_from_quote`)
  - **input**: JSON body
  - **expected status**: 201 / 403 / 404 / 409 / 422
  - **expected identity**: order create payload (incl. readiness snapshot)
  - **write risk**: **write**
  - **runtime data required**: accepted quote exists + gates satisfied

- **surface**: backend execution
  - **method**: POST
  - **URL**: `/api/v1/execution/plan-v2/preview/{order_id}`
  - **auth context**: permission-gated (`execution.plan_generate`)
  - **input**: `order_id`
  - **expected status**: 200 / 403 / 404 / 422
  - **expected identity**: `ExecutionPlanV2Preview` (`no_write=true`)
  - **write risk**: none (read-only by contract)
  - **runtime data required**: V2 order snapshot present

- **surface**: backend execution
  - **method**: POST
  - **URL**: `/api/v1/execution/plan-v2/from-order/{order_id}`
  - **auth context**: permission-gated (`execution.plan_generate`)
  - **input**: `order_id`
  - **expected status**: 200/201 / 403 / 404 / 422
  - **expected identity**: persist result
  - **write risk**: **write** (execution_plan row)
  - **runtime data required**: V2 order snapshot present

- **surface**: backend execution
  - **method**: POST
  - **URL**: `/api/v1/execution/plan-v2/materialize-tasks/{order_id}`
  - **auth context**: permission-gated (`execution.plan_generate`)
  - **input**: `order_id`
  - **expected status**: 201 / 403 / 404 / 409 / 422
  - **expected identity**: materialize result
  - **write risk**: **write** (mutates plan envelope only)
  - **runtime data required**: persisted v2 plan exists

---

### Frontend surfaces (for screenshots)

- **surface**: frontend
  - **method**: GET (navigation)
  - **URL**: `/product-system/products`
  - **auth context**: frontend auth-gated
  - **input**: none
  - **expected status**: 200
  - **expected identity**: catalog UI renders
  - **write risk**: none
  - **runtime data required**: templates available in backend

- **surface**: frontend
  - **method**: GET (navigation)
  - **URL**: `/product-system/products/:templateCode`
  - **auth context**: frontend auth-gated
  - **input**: `templateCode` in path
  - **expected status**: 200
  - **expected identity**: product detail UI renders with canonical identity
  - **write risk**: none
  - **runtime data required**: template exists

- **surface**: frontend
  - **method**: GET (navigation)
  - **URL**: `/product-system/blueprint-dossier`
  - **auth context**: frontend auth-gated (role-dependent UX)
  - **input**: template selection (UI)
  - **expected status**: 200
  - **expected identity**: dossier UI state (operator vs advanced/admin)
  - **write risk**: depends on available write controls; must prove backend rejection for operator
  - **runtime data required**: auth roles + dossier row optional

---

### Fixture/seed availability (runtime data)

- Commercial E2E fixture seed script:
  - `backend/scripts/seed_commercial_e2e_fixture.py`
  - Write risk: **write** (DB)
  - Constraint note: seeding is **not** executed in research; only mapped as a potential runtime prerequisite.

