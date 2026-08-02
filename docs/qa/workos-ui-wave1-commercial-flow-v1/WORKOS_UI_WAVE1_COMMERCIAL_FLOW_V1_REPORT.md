# WORKOS UI WAVE 1 — Commercial Flow V1 Report

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Track | **U1 only** |
| GO | UI Wave 1: Cereri → Produse → Oferte → Comenzi |
| Verdict | **PASS WITH WARNINGS** |
| Worktree | `C:\w\workos_ui_wave1_commercial_flow_v1` |
| Branch | `feat/ui-wave1-commercial-flow-v1` |
| Base | `c9ea5c0a` (App Shell Day Mode + Role Navigation Wave 0) |
| Frontend | `http://127.0.0.1:3030` (`VITE_ENABLE_DEV_AUTH=true`) |
| Backend | Existing `http://127.0.0.1:8000` (read-only UI consumption) |
| API identity | `BUILD_25` / `workos-staging-release-BUILD_25` / `environment=staging` / `git_commit=null` |
| QA DB copy | `backend/qa-dbs/ui_wave1_v1.db` (present; **not** used by the live `:8000` process in this run) |
| Commit message | `Transform commercial flow UI wave one` |
| Push | **NOT pushed** (Owner decision required) |

---

## 1. Verdict

**PASS WITH WARNINGS.**

The four commercial pages now share one visible story: **Cereri → Produse → Oferte → Comenzi**, with Romanian-first titles, flow strip + breadcrumbs, compact blockers, and diagnostics under **Detalii tehnice**. Backend gates/truth were not rewritten. Dev auth remains via `VITE_ENABLE_DEV_AUTH`.

---

## 2. Research answers (per zone)

### Cereri (`/intake`)

| Question | Answer |
|----------|--------|
| Cine folosește? | Sales / commercial / admin (role-projected nav). |
| Ce decizie? | Preia cererea, completează date, marchează gata pentru ofertă. |
| Sursă de adevăr | Backend intake list (`Live DB` in runtime). |
| Acțiune principală | Deschide spațiul cererii / creează ofertă când statusul o permite. |
| Ce urmează? | Produs configurat → Ofertă. |
| Blocante | Lipsa câmpurilor / sursă non-live — compacte, chromeBanner. |
| Diagnostic | Timeline / status / template under **Detalii tehnice**. |
| Termeni de ascuns | „Work Intake” ca H1 (înlocuit cu **Cereri**). |
| Link contextual | Flow strip + NextStepPanel → Produse / Oferte. |
| Duplicate | Header EN vs nav RO (rezolvat). |
| Dark islands | Status/banner night stacks → day-aware tokens. |
| Shared reuse | PageShell, FlowBreadcrumb, CommercialFlowStrip, NextStepPanel, chromeBanner. |
| Nu schimba | Create/status mutation paths, Intake V6 deep workspace. |

### Produse (`/product-system/products` + template detail)

| Question | Answer |
|----------|--------|
| Cine folosește? | Admin produs / commercial care verifică template-ul. |
| Ce decizie? | Alege / inspectează structura produsului (nu preț client). |
| Sursă | Product templates + availability (backend). |
| Acțiune principală | Selectează template → Structură produs. |
| Ce urmează? | Continuă spre ofertă din Cereri/Oferte (nu din PS). |
| Blocante | Honesty banners rămân, demote în Detalii tehnice. |
| Diagnostic | Truth chips + MODULE_MODEL_DEFERRED under disclosure. |
| Termeni | H1 **Produse**; listă „Produse active”. |
| Link | NextStepPanel → Oferte / Cereri; flow strip. |
| Nu schimba | SVG/DXF parsers, Product Truth writes, Pricing. |

### Oferte (`/quotes` + detail)

| Question | Answer |
|----------|--------|
| Cine? | Commercial / admin. |
| Decizie | Trimite / acceptă intern / convertește — conform contractului existent. |
| Sursă | Quotes API + readiness backend. |
| Acțiune | Selectează ofertă; acțiuni din panou (fără auto-accept). |
| Urmează | Comandă după acceptare/conversie. |
| Blocante | Readiness gate rămâne backend; UI compact. |
| Diagnostic | Policy CostEngine under **Detalii tehnice**. |
| RO labels | Draft→**Ciornă**, Priced→**Tarifat**. |
| Link | Flow strip; empty panel → Cereri/Produse; accepted → Comenzi. |
| Nu schimba | Conversion/accept handlers, readiness policy. |

### Comenzi (`/orders` + detail)

| Question | Answer |
|----------|--------|
| Cine? | Commercial / ops lead. |
| Decizie | Confirmă / pregătește execuție — fără re-pricing. |
| Sursă | Orders API + frozen snapshot. |
| Acțiune | Selectează comandă; next-step spre execuție când există plan. |
| Urmează | Execuție / Shop Floor (out of Wave 1 redesign). |
| Diagnostic | Readiness-at-acceptance under **Detalii tehnice** (was dark `#0D1E0D` island). |
| Link | Ofertă sursă; empty → Oferte/Cereri. |
| Nu schimba | Plan generation mutation semantics; Inventory. |

---

## 3. Before / after opinion (agent)

**Before:** Nav already said Cereri/Produse/Oferte/Comenzi (Wave 0), but pages disagreed — H1 „Work Intake” / „Product System”, badge flood on Produse, EN Draft/Priced, dark chips (`bg-slate-800`), readiness banner as primary chrome, weak cross-links.

**After:** In ~5 seconds the operator sees where they are (flow strip + RO title), what the page is for (subtitle), and the next commercial step (NextStepPanel). Diagnostics are secondary. Day mode reads as light on these surfaces.

**Honest residual:** Quote list still shows `0,00 RON` on some accepted cards while KPIs show large totals (display honesty debt — not fixed here; no business-truth rewrite). Detail deep-link click harness is brittle (list cards are `div` click targets). Product spine still mixes EN step names (`Product Template`, `Product Compiler`) — acceptable as domain labels under RO page chrome.

---

## 4. Flow continuity

| Link | Present | Bypass? |
|------|---------|---------|
| Cereri → Produse | Yes (strip + next step) | No mutation |
| Produse → Oferte | Yes (next step) | Does not create quote |
| Oferte → Comenzi | Yes (accepted next step / empty guidance) | Convert still gated |
| Comenzi → Ofertă sursă | Yes (contextual next step when `quoteId`) | Read-only navigate |
| Breadcrumbs include Produse | Yes on Oferte/Comenzi/Produse | — |

**Continuity verdict: COHERENT** for operator orientation. Business gates unchanged.

---

## 5. Day / dark

| Axis | Result |
|------|--------|
| Day mode on U1 pages | Improved — light surfaces, chromeBanner, wo-* tokens; dark hex islands on order readiness removed |
| Dark mode | Captured; NextStepPanel/chromeBanner have dark: variants; no major regression observed |
| Remaining islands | Some list-row EN channel labels; Product spine EN step chips; Quote KPI vs card amount mismatch; shell theme icon still moon-in-light (Wave 0 residual) |

---

## 6. Dev Mode proof

- FE started with `VITE_ENABLE_DEV_AUTH=true` on `:3030`.
- Capture used Bearer `__DEV_BYPASS_TOKEN__` + `WORKOS_DEV_GUARD_BYPASS=1`.
- Pages loaded authenticated as staging user chrome (`DA`) without forcing production auth.
- No AuthContext / shellNavigation edits in this track.

---

## 7. Screenshots

### Before (`screenshots/before/{light,dark}/`)

- `01-cereri.png`, `02-produse.png`, `03-oferte.png`, `04-comenzi.png`

### After (`screenshots/after/{light,dark}/`)

- Lists: `01-cereri.png` … `04-comenzi.png`
- Details / selection attempts: `01b-cerere-detaliu.png`, `02b-produs-detaliu.png`, `03b-oferta-detaliu.png`, `04b-comanda-detaliu.png`

Harness: `_u1_capture.mjs` (Playwright via `createRequire` from `frontend/package.json`).

---

## 8. Files changed (allowlist)

| Path | Role |
|------|------|
| `frontend/src/lib/commercialFlowUi.ts` | Pure helpers + RO labels |
| `frontend/src/lib/commercialFlowUi.test.ts` | Targeted vitest |
| `frontend/src/components/workos/CommercialFlowStrip.tsx` | Flow rail |
| `frontend/src/components/workos/TechnicalDetailsDisclosure.tsx` | Detalii tehnice |
| `frontend/src/components/workos/FlowBreadcrumb.tsx` | Produse in spine crumbs |
| `frontend/src/components/workos/NextStepPanel.tsx` | Day-mode chrome |
| `frontend/src/pages/WorkIntake.tsx` | Cereri hierarchy |
| `frontend/src/pages/Quotes.tsx` | Oferte hierarchy |
| `frontend/src/pages/Orders.tsx` | Comenzi hierarchy |
| `frontend/src/pages/WorkIntake.badges.test.tsx` | Expect Cereri + Auth mock |
| `frontend/src/pages/Orders.empty.test.tsx` | Cereri CTA label |
| `frontend/src/features/product-system/ProductSystemLayout.tsx` | Produse chrome |
| `frontend/src/features/product-system/ProductSystemV2Workspace.tsx` | Diagnostics demotion |
| `frontend/src/features/product-system/productSystemBlankWorkspaceIa.test.ts` | IA expectation update |
| `docs/qa/workos-ui-wave1-commercial-flow-v1/**` | Report + screenshots + harness |
| `docs/worklog/realignment/2026-08-02_ui_wave1_commercial_flow_v1.md` | Worklog |

**Not touched:** AppShell, shellNavigation, AuthContext, App.tsx router, global theme CSS, backend/**, Ops-Graph, Employee Mobile, Intake V6 deep rewrite.

---

## 9. Tests

### Run (green)

```text
pnpm exec vitest run \
  src/lib/commercialFlowUi.test.ts \
  src/features/product-system/productSystemBlankWorkspaceIa.test.ts \
  src/pages/WorkIntake.badges.test.tsx \
  src/pages/Orders.empty.test.tsx
→ 18 passed
```

### Not run (report only)

- Full `pnpm run test` / `test:ci`
- Frontend lint/build CI quartet
- Backend pytest
- E2E Playwright product suites

---

## 10. Warnings / blockers

1. Live API `:8000` was an **existing** staging process (`git_commit=null`), not the worktree QA DB — documented; UI remained read-only.
2. Quote amount display mismatch (KPI vs card `0,00 RON`) remains.
3. Detail capture via click selectors is imperfect for Quotes/Orders list cards.
4. Product System authoring/spine still exposes some EN domain labels inside the page body.

---

## 11. Boundaries respected

- No auto-accept, auto-order, repricing, readiness bypass.
- No business truth invented in UI.
- No route deletion.
- No global shell/theme ownership breach.
- No graphic file parsing in Product System.

---

## 12. Score

**Cât sunt în direcția stabilită: 78/100%**

Wave 0 shell + this commercial continuity put the operator spine in place. Remaining debt is display honesty (quote totals), deeper EN domain labels inside Product System, and Wave 2 production surfaces.

---

## 13. Next

- **UI Wave 2:** Execution / Shop Floor / Control producție clarity (separate GO).
- **Functional:** Owner policy for employee actual cost / material actuals → Profitability Complete (Track P — separate ownership).
