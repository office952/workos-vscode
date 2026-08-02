# WORKOS FULL ROUTE UI/UX BASELINE V1 REPORT

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| GO | Full Route UI/UX Baseline V1 |
| Verdict | **PASS WITH WARNINGS** |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD at GO start | `75e31d46` |
| Worktree | `C:\w\psiso` |
| Frontend | `http://127.0.0.1:3000` |
| Backend | `http://127.0.0.1:8000` |
| Database | `backend/dev.db` |
| Boundary | **Documentation + screenshots only** — no product code, DB, theme, CSS, or component changes; **no shell rewrite** in this GO |
| Deliverables | `route-inventory.md` · `page-scorecard.md` · this report · worklog under `docs/worklog/realignment/` |

---

## 1. Verdict

**PASS WITH WARNINGS.**

The route surface was inventoried from `frontend/src/App.tsx`, opened via U1/U2 capture harnesses against a live staging stack, and photographed under day-mode (`themeClass: light` in U2). Warnings are accepted by design:

1. **Inaccessible parametric states were not mutated** (client workspace, employee profile, many PS structure deep links).
2. **Day mode is imperfect** (sidebar often cool/dark-grey vs light content; Employee Mobile standalone remains dark).
3. **Jargon and EN/RO mix** are systemic in chrome and page titles — documented, not “fixed” here.

This GO does **not** claim production polish or percent-complete product readiness.

---

## 2. Counts

| Metric | Value |
|--------|------:|
| App.tsx `path=` Route declarations | 78 |
| + Product System `index` route | 1 |
| **Total Route elements** | **79** |
| Product-relevant named patterns (excl. auth + `*`) | **72** |
| Standalone apps | 3 (`employee-app`, `employee-app-v2`, `intake-v6-app`) |
| Redirect-only shell aliases | 10 |
| U1 pages captured | 12 |
| U2 pages captured | 29 |
| Unique capture paths (U1∪U2) | **38** |
| Screenshot PNG files | **45** |
| Drill inaccessible (no mutation) | 2 |

Details: [`route-inventory.md`](./route-inventory.md). Scores: [`page-scorecard.md`](./page-scorecard.md).

---

## 3. Shell findings

Evidence: `screenshots/shell/00-app-shell-chrome.png`, `01-dashboard-control-tower.png`, and every U2 `bodyPreview`.

### 3.1 Day mode / sidebar

- U2 consistently reports `themeClass: "light"`.
- Main canvas is light; **sidebar frequently reads as slate / cool grey** (darker than page body) — “day mode” is incomplete as a visual system.
- Theme toggle present (moon icon while light is active) — chrome metaphor is easy to misread.
- Employee Mobile routes ignore shell day mode (standalone dark UI) — **out of scope** for product change; document as DEFER.

### 3.2 Romanian / English mix

Sidebar groups are Romanian (`OPERAȚIUNI`, `COMERCIAL`, `RESURSE`, `PERSONAL`, `SISTEM`) while many leaves stay English: **Control Tower**, **Shop Floor**, **Operator**, **Work Intake**, **Product System**, **Pricing**. Search placeholder is fully English. Page H1s often diverge from nav (e.g. Document Center, Operator View, Operational Reports, Pricing Registry).

### 3.3 “Registry” exposure

Nav and titles expose internal vocabulary:

- `Pricing (registry)`
- `Utilaje (registry)`
- `Pontaj (registry intern)`
- H1s: “Pricing Registry”, “Utilaje (registry)”

Operators should not need the word **registry** to find prices or machines.

### 3.4 Ops surface overlap

Five concurrent “live work” homes for a privileged admin:

1. Control Tower  
2. Shop Floor  
3. Operator  
4. Execuție (+ Ops-Graph, Reality Review)  
5. Atelier Tablet  

(+ Employee Mobile standalone, deferred)

Baseline disposition: **KEEP** each route’s technical role, but Wave 0 must **role-gate and rename** so one persona does not see all five as peers.

### 3.5 Ops-Graph (Track F)

`/execution/ops-graph` = **KEEP**. Controlled employee assignment UI is emerging on parallel Track F. Baseline notes interaction presence only — **do not redesign** assignment here.

---

## 4. Day-mode systemic findings (`themeClass: light`)

| Finding | Severity | Wave |
|---------|----------|------|
| Sidebar vs content luminance mismatch | High | 0 |
| English search + mixed nav leaves | High | 0 |
| `(registry)` in primary nav | High | 0 |
| Admin/HR/money/demo items visible to broad admin chrome | High | 0 |
| Dense yellow audit banners on Control Tower | Medium | 1 |
| Internal codes on Shop Floor columns (`METAL_FAB`, etc.) | Medium | 2 |
| Ops-Graph / Reality Review expert jargon | Medium | 2–3 (clarity only; no redesign Track F) |
| Employee Mobile dark + EN error strings | Medium | DEFER |
| Demo routes reachable | Medium | 0 (hide) |

---

## 5. Top 10 user-facing problems

1. **Too many parallel ops homes** — Control Tower / Shop Floor / Operator / Execuție / Tablet compete without role story.  
2. **Day mode incomplete** — light content + darker sidebar + confusing theme icon.  
3. **“(registry)” jargon in primary navigation** — Pricing, Utilaje, Pontaj.  
4. **Systemic EN/RO split** — groups RO, leaves EN; H1 ≠ sidebar.  
5. **Sensitive PERSONAL items always visible** — payments, advances, HR evidence in full chrome.  
6. **Demos & lab surfaces** — commercial-spine / volumetric preview / output-blocks / blueprint dossier look like product peers.  
7. **Control Tower audit chrome** — gap banners + ACTUAL/PROXY/DERIVAT overwhelm first viewport.  
8. **Shop Floor internal WC keys** — `CNC_ROUTING`, `LETTER_FORMING`, truncated labels.  
9. **Employee Mobile** — technical English errors; not integrated with shell IA (DEFER change).  
10. **Deep links not operator-discoverable** — client workspace / employee profile require mutation or missing affordances (accepted warning).

---

## 6. Separate readiness scores (honest)

| Axis | Score / statement |
|------|-------------------|
| **Architecture direction** | **3 / 5** — Commercial spine + Execution + Product System boundaries are recognisable; freeze/reference discipline exists |
| **Functional spine** | **3 / 5** — Intake → Quotes → Orders → Execution opens and carries fixture work; capacity/assignment still evolving (Track F) |
| **UI/UX readiness** | **2 / 5** — Expert-usable staging UI; day-mode + language + IA overload block operator clarity |
| **Production readiness** | **not yet measurable** — no claim of shop-floor go-live; staging badges, gaps, and role model incomplete |
| **Overall product completion** | **not yet measurable** — **never invent “97% complete”**; this baseline refuses fake completion percentages |

Captured-page mean UX score ≈ **2.5 / 5** (see scorecard). That is a UI honesty metric, not a company OKR.

---

## 7. Waves 0–5 backlog

### Wave 0 — App Shell + Day Mode Foundation + Role-Based Navigation  
**Serial prerequisite for later UI waves.**  
Scope (future GO — not this docs GO): unify day-mode sidebar/tokens; Romanian-first nav labels; strip “(registry)” from primary chrome; role-based hide for HR/money/demos/lab; clarify which single ops home each role sees first.  
**Parallel OK:** copy inventory of labels; screenshot re-baseline.  
**Serial:** token/theme decisions before page-level restyles.

### Wave 1 — Control Tower & commercial first-run clarity  
Collapse audit banners; align H1↔nav; quick actions match role.  
**After** Wave 0 shell tokens. Parallel: Quotes/Orders list chrome only.

### Wave 2 — Shop Floor + Tablet operator language  
Human WC names; truncation; live status literacy. Parallel with Wave 1 if shell tokens frozen.

### Wave 3 — Execution cluster clarity (no Track F redesign)  
Breadcrumb/IA story among Execuție / Ops-Graph / Reality Review; jargon reduction **without** changing assignment interaction owned by Track F. Serial with Track F merge etiquette.

### Wave 4 — Registries & Product System operator vs admin  
Rename Pricing/Utilaje; ADMIN_ONLY for blueprint/output-blocks/planned PS sections. Parallel with Wave 3 on different owners.

### Wave 5 — Employee Mobile + deep-link discoverability  
**DEFER product change until explicit GO.** Visibility: ADMIN_ONLY / hide from main shell. Later: day-mode parity, RO errors, task materialization honesty.

---

## 8. Boundaries respected

| Allowed this GO | Forbidden this GO |
|-----------------|-------------------|
| Markdown docs under `docs/qa/…` and worklog | Product code, components, CSS, theme tokens |
| Screenshot evidence already on disk | DB mutations to unlock deep links |
| Honest dispositions & scores | Shell rewrite / nav implementation |
| Note Track F Ops-Graph assignment | Redesign Ops-Graph assignment UX |
| Leave `_tmp*` / capture `.mjs` on disk | Emphasize them as commit deliverables |

---

## 9. Artifacts

### Deliverables (this package)

- `docs/qa/workos-full-route-uiux-baseline-v1/route-inventory.md`
- `docs/qa/workos-full-route-uiux-baseline-v1/page-scorecard.md`
- `docs/qa/workos-full-route-uiux-baseline-v1/WORKOS_FULL_ROUTE_UIUX_BASELINE_V1_REPORT.md`
- `docs/worklog/realignment/2026-08-02_workos_full_route_uiux_baseline_v1.md`
- `docs/qa/workos-full-route-uiux-baseline-v1/screenshots/**` (evidence)

### Tooling artifacts (keep local; prefer not to commit)

- `_u1_capture.mjs`, `_u2_capture.mjs`, `_u1_capture_details.mjs`, `_u2_drill.mjs`
- `_u1_capture_inventory.json`, `_u2_capture_results.json`, `_u2_drill_results.json`
- `_tmp*` helpers

---

## 10. Mini-decizie

Wave 0 is the only honest next product step for UI: **shell + day mode + role nav**. Until that lands, page-level polish will keep fighting a confusing chrome. Functional spine work (Capacity / Track F assignment) may proceed in parallel **without** pretending UI/UX readiness is high.
