# WorkOS Full Route UI/UX Baseline V1 — Route Inventory

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Status | **PASS WITH WARNINGS** |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD at GO start | `75e31d46` |
| Worktree | `C:\w\psiso` |
| Runtime | FE `http://127.0.0.1:3000` · BE `http://127.0.0.1:8000` · DB `backend/dev.db` |
| Source of routes | `frontend/src/App.tsx` |
| Capture sources | `_u1_capture_inventory.json`, `_u2_capture_results.json`, `_u2_drill_results.json` |
| Boundary | Docs + screenshots only — **no product code / shell rewrite in this GO** |

---

## 1. Route counts (App.tsx)

| Bucket | Count | Notes |
|--------|------:|-------|
| `<Route path="…">` declarations | **78** | Entire `App.tsx` tree |
| `<Route index>` (Product System) | **1** | `/product-system` index redirect |
| **Total Route elements (path + index)** | **79** | |
| Catch-all `*` | 3 | AppShell, AuthenticatedAppRoutes, AuthGate |
| Auth plumbing | 4 | `/auth/callback`, `/auth/error`, `/auth/logout`, `/logout-callback` |
| **Product-relevant named patterns** | **72** | 78 − 3 catch-alls − 4 auth **+ 1 index** |
| AppShell named paths (incl. `/` + nested PS relatives) | **67** | Through `/settings` |
| Product System nested children (relative) | **15** | `products` … `advanced` |
| Product System structure detail variants | **7** | Letters/ACM structure pages + `:stepId` |
| Standalone apps | **3** | `/employee-app/*`, `/employee-app-v2/*`, `/intake-v6-app/*` |
| Intake V6 nested under standalone | **2** | `operator`, `:workspaceId/operator` (duplicate surface) |
| Redirect-only shell paths | **10** | See §3 |

**Capture / screenshot coverage**

| Metric | Count |
|--------|------:|
| U1 capture entries | 12 |
| U2 capture entries | 29 |
| Unique paths in U1∪U2 JSON | **38** (3 overlaps: `/operator`, `/intake-v6/operator`, `/product-system/components`) |
| Screenshot PNG files on disk | **45** |
| U2 drill opened | 1 (`/tablet/cnc`) |
| U2 drill inaccessible (no mutation) | 2 (`/clients/:clientName`, `/employees-records/:id`) |

Tooling artifacts left on disk (not deliverables): `_u1_capture.mjs`, `_u2_capture.mjs`, `_u1_capture_details.mjs`, `_u2_drill.mjs`, `_tmp*`, capture JSON helpers. Prefer **not** committing them.

---

## 2. Sidebar labels (from U2 `bodyPreview`, day mode / `themeClass: light`)

Observed IA groups (admin session “DA” / Dev Admin):

| Group | Labels |
|-------|--------|
| **OPERAȚIUNI** | Control Tower · Shop Floor · Operator · Atelier Tablet |
| **COMERCIAL** | Clienți · Work Intake · Oferte · Comenzi · Execuție · Documente |
| **RESURSE** | Inventar & OC · Pricing **(registry)** · Product System · Colaboratori · Utilaje **(registry)** · Rapoarte |
| **PERSONAL** | Angajați operaționali · Evidență internă HR · Pontaj **(registry intern)** · Plăți angajați · Avansuri / Datorii |
| **SISTEM** | Harta sistemelor · Guvernanța sistemului · Setări |

Chrome also shows English search placeholder: `Search jobs, tasks, machines…`.

---

## 3. Redirects & inaccessible (baseline)

### Redirects observed / declared

| From | To | Evidence |
|------|----|----------|
| `/` | `/dashboard` | App.tsx |
| `/personal` | `/employees` | App.tsx + U2 capture |
| `/pricing` | `/inventory/pricing` | App.tsx + U2 capture |
| `/products` | `/product-system/products` | App.tsx |
| `/templates` | `/product-system/products` | App.tsx |
| `/inventory/material-price-registry` | `/inventory/pricing` | App.tsx |
| `/inventory/commercial-markup-policy` | `/inventory/pricing` | App.tsx |
| `/inventory/productsystem-pricing-preview` | `/inventory/pricing` | App.tsx |
| `/product-system` (index) | products default | App.tsx `ProductSystemIndexRedirect` |
| `/product-system/dossier-completion` | `/product-system/blueprint-dossier` | App.tsx |
| `/intake-v6/operator` | `/intake-v6/:workspaceId/operator` | U1/U2 capture (workspace auto-pick) |
| unknown `*` (shell) | `/dashboard` | App.tsx |

### Inaccessible without mutation (accepted warning)

| Path | Reason |
|------|--------|
| `/clients/:clientName` | No client row/link navigable without mutating data (`_u2_drill_results.json`) |
| `/employees-records/:employeeId` | Profile deep-link not found as navigable control |
| Many PS structure detail URLs | Require specific `templateCode` + structure step; not mass-opened in U1/U2 |
| `/quotes/:quoteId`, `/orders/:orderId`, `/execution/:order_id`, `/intake/:id` | Parametric; only list parents + selected drill targets captured |
| `/tablet/:stationId/:taskId` | Needs live station+task; only `/tablet` + `/tablet/cnc` opened |

---

## 4. Disposition legend

`KEEP` · `RENAME` · `MOVE` · `MERGE` · `HIDE_BY_ROLE` · `ADMIN_ONLY` · `LEGACY_LABEL` · `DEFER` · `REMOVE_CANDIDATE_ONLY`

---

## 5. Full disposition table

### 5.1 Shell / operations

| Route | Sidebar / title | Captured | Disposition | Note |
|-------|-----------------|----------|-------------|------|
| `/dashboard` | Control Tower | ✅ shell + U1 | **KEEP** + **RENAME?** | English “Control Tower” vs RO chrome; primary ops home |
| `/shop-floor` | Shop Floor | ✅ | **KEEP** + **LEGACY_LABEL** | Overlaps Execuție / Operator mental model |
| `/operator` | Operator | ✅ U1+U2 | **KEEP** + **HIDE_BY_ROLE** | Distinct from Execuție; role-gate later |
| `/tablet` | Atelier Tablet | ✅ | **KEEP** | Station selector |
| `/tablet/:stationId` | (drill) | ✅ `/tablet/cnc` | **KEEP** | |
| `/tablet/:stationId/:taskId` | — | ❌ | **KEEP** | Not opened; leave intact |
| `/execution` | Execuție | ✅ | **KEEP** | Commercial→ops spine |
| `/execution/ops-graph` | Ops graph | ✅ | **KEEP** | Track F controlled assignment UI emerging — **do not redesign in baseline** |
| `/execution/reality-review` | Reality review | ✅ | **KEEP** + **ADMIN_ONLY?** | Dense audit surface |
| `/execution/:order_id` | Execution detail | ✅ screenshots `08b`/`08c` | **KEEP** | |

### 5.2 Commercial spine

| Route | Sidebar / title | Captured | Disposition | Note |
|-------|-----------------|----------|-------------|------|
| `/clients` | Clienți | ✅ | **KEEP** | |
| `/clients/:clientName` | Client workspace | ❌ inaccessible | **KEEP** | Warning only |
| `/intake` | Work Intake | ✅ | **KEEP** + **LEGACY_LABEL** | English label in RO nav |
| `/intake/:id` | Legacy intake route | ❌ | **LEGACY_LABEL** / **DEFER** | Parametric; V6 is active operator flow |
| `/quotes` | Oferte | ✅ | **KEEP** | |
| `/quotes/:quoteId` | — | ❌ | **KEEP** | |
| `/orders` | Comenzi | ✅ | **KEEP** | |
| `/orders/:orderId` | — | ❌ | **KEEP** | |
| `/documents` | Documente / “Document Center” | ✅ | **KEEP** + **RENAME** | H1 English vs sidebar RO |

### 5.3 Intake V6 / demos

| Route | Captured | Disposition | Note |
|-------|----------|-------------|------|
| `/intake-v6/operator` | ✅ redirect | **KEEP** | Auto-selects workspace |
| `/intake-v6/:workspaceId/operator` | ✅ | **KEEP** | Canonical V6 operator |
| `/intake-v6-app/*` | ❌ (standalone) | **ADMIN_ONLY** / **DEFER** | Standalone dark shell; not in main nav |
| `/demo/commercial-spine` | ✅ | **ADMIN_ONLY** / **HIDE_BY_ROLE** | Internal demo |
| `/demo/volumetric-letter-preview` | ✅ | **ADMIN_ONLY** / **HIDE_BY_ROLE** | QA demo |

### 5.4 Product System

| Route | Captured | Disposition | Note |
|-------|----------|-------------|------|
| `/product-system` (index) | redirect | **KEEP** | |
| `/product-system/products` (+ `:templateCode`) | ✅ | **KEEP** | Primary PS surface |
| Structure detail routes (7) | ❌ mass | **KEEP** / **DEFER** UX polish | Laboratory depth; freeze-aware |
| `/product-system/components` | ✅ | **KEEP** + **DEFER** | Planned section page |
| `resources` / `operations` / `dependencies` / `validation` / `advanced` | ❌ | **DEFER** | Planned placeholders |
| `/product-system/blueprint-dossier` | ✅ | **ADMIN_ONLY** | Studio |
| `/product-system/output-blocks-preview` | ✅ | **ADMIN_ONLY** | Preview |
| `/product-system/dossier-completion` | redirect | **REMOVE_CANDIDATE_ONLY** | Legacy alias only |
| `/products`, `/templates` | redirect | **LEGACY_LABEL** | Keep aliases |

### 5.5 Registries / resources

| Route | Captured | Disposition | Note |
|-------|----------|-------------|------|
| `/inventory` | ✅ | **KEEP** | |
| `/inventory/pricing` | ✅ | **KEEP** + **RENAME** | Drop “(registry)” in nav |
| pricing legacy redirects (3) | — | **LEGACY_LABEL** | Keep redirects |
| `/pricing` | ✅ redirect | **LEGACY_LABEL** | |
| `/utilaje` | ✅ H1 “Utilaje (registry)” | **KEEP** + **RENAME** | Registry jargon in H1 + nav |
| `/colaboratori` | ✅ | **KEEP** | |
| `/reports` | ✅ | **KEEP** | |
| `/reports/operational` | ✅ H1 “Operational Reports” | **KEEP** + **RENAME** | EN H1 |

### 5.6 People / HR

| Route | Captured | Disposition | Note |
|-------|----------|-------------|------|
| `/employees` | ✅ | **KEEP** | |
| `/personal` | ✅ redirect | **LEGACY_LABEL** | |
| `/employees-records` | ✅ | **KEEP** + **HIDE_BY_ROLE** | HR |
| `/employees-records/:employeeId` | ❌ | **KEEP** | Inaccessible warning |
| `/attendance` | ✅ | **KEEP** + **RENAME** | Nav: “Pontaj (registry intern)” |
| `/attendance/effects` | ✅ | **KEEP** + **HIDE_BY_ROLE** | |
| `/employee-payments` | ✅ | **HIDE_BY_ROLE** | Sensitive |
| `/employee-advances` | ✅ | **HIDE_BY_ROLE** | Sensitive |

### 5.7 Employee Mobile (out of scope for product change)

| Route | Captured | Disposition | Note |
|-------|----------|-------------|------|
| `/employee-app/*` | ✅ | **DEFER** + **ADMIN_ONLY** visibility | Standalone; dark UI; technical error banner; **no product change in this GO** |
| `/employee-app-v2/*` | ✅ | **DEFER** + **ADMIN_ONLY** visibility | Same boundary |

### 5.8 System / admin

| Route | Captured | Disposition | Note |
|-------|----------|-------------|------|
| `/modules` | ✅ Harta sistemelor | **ADMIN_ONLY** | |
| `/governance` | ✅ | **ADMIN_ONLY** | |
| `/settings` | ✅ | **KEEP** | |

### 5.9 Auth (non-IA)

| Route | Disposition |
|-------|-------------|
| `/auth/*`, `/logout-callback` | **KEEP** (infra; out of UI baseline scoring) |

---

## 6. Overlap map (operator mental model)

Surfaces that compete for “where do I run production today?”:

```text
Control Tower (/dashboard)
    ↕ KPI / gaps / quick actions
Shop Floor (/shop-floor)
    ↕ live machines
Operator (/operator)
    ↕ operator queue
Execuție (/execution) → Ops-Graph / Reality Review / :order_id
Atelier Tablet (/tablet)
Employee Mobile (/employee-app*)   ← DEFER / out of shell IA for now
```

Baseline recommendation: **KEEP all**, but Wave 0 must clarify roles + labels so operators are not offered five “live ops” homes at once.

---

## 7. Ops-Graph note (Track F parallel)

`/execution/ops-graph` disposition remains **KEEP**. Controlled employee assignment interaction is emerging on a parallel Track F. This baseline audits presence and IA placement only — **no redesign**, no assignment UX rewrite in this GO.
