# AGENTS.md — WorkOS agent guide



Read this before editing the WorkOS monorepo. Human developers can use it too.



## 0. Current WorkOS reference freeze



**Status: `CURRENT_WORKOS_FROZEN_AS_REFERENCE` — PASS**



Declaration: [`docs/freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md`](docs/freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md) · Manifest: [`docs/freeze/CURRENT_WORKOS_REFERENCE_FREEZE_MANIFEST.json`](docs/freeze/CURRENT_WORKOS_REFERENCE_FREEZE_MANIFEST.json).



Product System laboratory feature work is **closed** at production cost / EIC. This repository is historical laboratory / reference evidence.



Canonical Workflow-ADV contracts: [`docs/workflow-adv/README.md`](docs/workflow-adv/README.md).



Before any Workflow-ADV **implementation** work, read [`docs/architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md`](docs/architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md) (Cursor rule: `.cursor/rules/workflow-adv-smart-code.mdc`). Smart Code is **not** yet a mandatory CI stack — product code in Workflow-ADV remains **blocked** until `WORKFLOW_ADV_SMART_CODE_ENFORCEMENT_BOOTSTRAP` is accepted.



Post-freeze changes in this repo are limited to reference correction, evidence preservation, security/emergency repair, or explicit owner instruction `CURRENT_WORKOS_REFERENCE_FREEZE_OFF`. Do **not** expand Product System features, Lab UI, offer/Execution, Supplier Import, or in-repo SVG/DXF/DWG parsers without that unfreeze.



## 1. Prime directive



1. **Do not assume** — inspect code, env, and docs when unsure.

2. **Inspect before changing** — trace imports, template config, and handoff paths.

3. **Keep scope narrow** — no drive-by refactors; match the active build boundary.

4. **Run relevant tests** — targeted commands for your change area; see validation truth below.

5. **Respect boundaries** — see protected areas and “Do not do” below.



When a build spec exists under `docs/qa/BUILD_*.md`, follow its stated boundary.



## 1.1 Logic placement, assisted interpretation, and operator confirmation

For volumetric letters artwork and Product Truth:

1. **Desktop analysis app observes** — all SVG/DWG/DXF (and other graphic) file intelligence lives outside WorkOS. Do **not** implement or extend WorkOS parsers/analyzers/auto-grouping.
2. **WorkOS consumes** a versioned external structured result (observed/proposed only); validates contract/provenance; never treats it as Product Truth authority.
3. **AI may interpret** (future assistant) — proposes and asks; **never** writes Product Truth, Pricing, CostEngine, Offer, Order, Execution, or production handoff.
4. **Operator confirms** — only confirmed truth is saved.
5. **Honesty when uncertain** — stop and ask the smallest useful question; do not invent groups, fuzzy-match, or ship unconfirmed truth into pricing.
6. **Initial grouping modes** — operator declares `by_layer` or `by_color`; do not auto-mix methods. Layer/color names and fixture labels (e.g. Maria, Soare) are observations/test data, not domain identity.
7. **Confirmed-case learning** — save versioned, auditable precedents for reuse; global model changes require dataset/eval/owner GO, not a single click.
8. **Deterministic validation** of the **consumed** external payload remains mandatory; geometric correctness of the desktop parse is not a WorkOS readiness claim.

Canonical ownership: [`docs/architecture/artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md`](docs/architecture/artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md). Teaching semantics: [`docs/architecture/artwork-understanding/2026-07-20_ARTWORK_UNDERSTANDING_OPERATOR_TEACHING_MODEL.md`](docs/architecture/artwork-understanding/2026-07-20_ARTWORK_UNDERSTANDING_OPERATOR_TEACHING_MODEL.md). Build 2 GO suspended pending re-audit: [`docs/plans/2026-07-20_WORKOS_VOLUMETRIC_LETTERS_BUILD2_LOGIC_REALIGNMENT_ADDENDUM.md`](docs/plans/2026-07-20_WORKOS_VOLUMETRIC_LETTERS_BUILD2_LOGIC_REALIGNMENT_ADDENDUM.md).



## 2. Canonical commands



Ports: backend **8000**, frontend **3000**.



Root scripts use **`npx pnpm@8.10.0`** — global `pnpm` is not required. Backend scripts reuse **`backend/.venv`** when present, else resolve Python via **`WORKOS_PYTHON` → `python` → `py -3`**.



### From repo root (`package.json`)



| Script | Action |

|--------|--------|

| `npm run dev:frontend` | Vite dev server (via npx pnpm) |

| `npm run dev:backend` | uvicorn + injected env (PowerShell helper) |

| `npm run dev:stack` | Full stack via `scripts/start-dev.ps1` |

| `npm run validate:frontend` | lint + typecheck + build — **currently FAIL (TS debt)** |

| `npm run test:frontend` | Full Vitest suite (prefer targeted files) |

| `npm run test:backend` | pytest (installs `requirements-dev.txt` first) |

| `npm run test:e2e:workintake-finish` | Playwright finish-display smoke |

| `npm run template-lifecycle:validate` | Template lifecycle gate (local; exit 2 on required BLOCKED) |



### Validation truth



| Gate | Status | Agent guidance |

|------|--------|----------------|

| `validate:frontend` | **FAIL** (~85 TS errors) | Intended full gate; do **not** declare frontend validation green |

| Targeted Vitest | Use for scoped frontend builds | Example below |

| Full `test:frontend` | Noisy | Not the current repo gate |

| Full `test:backend` | Known failures exist | Prefer targeted pytest files |

| E2E finish smoke | Passes when seeded + stack live | See E2E section |

| `template-lifecycle:validate` | Local gate ready; **no real CI pipeline in-repo yet** | Run before template-affecting work; currently fails on Metal Premount baseline until dedicated GO |



Next recommended build: **Frontend Typecheck Debt Audit** (separate from feature work).



### Targeted frontend test (preferred)



```powershell

npm run test:frontend -- src/lib/colorRegistry/colorRegistry.test.ts

```



Or:



```powershell

cd frontend

npx --yes pnpm@8.10.0 exec vitest run src/lib/volumetricFinishDisplay.test.ts

```



### Backend dev



Helper path (injects env, creates venv if needed):



```powershell

npm run dev:backend

```



Manual path — **you must set env vars** (helpers inject; uvicorn alone does not load `backend/.env`):



```powershell

cd backend

$env:APP_ENV='development'

$env:ENVIRONMENT='development'

$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'

$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'

.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

```



If Python is not on PATH: `$env:WORKOS_PYTHON='C:\Path\To\python.exe'` then re-run helper scripts.



### Backend pytest



```powershell

npm run test:backend

```



Targeted subset:



```powershell

cd backend

.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_quote_ready_policy.py -q

```



### E2E finish smoke



**Prerequisites:**



1. Seed fixture (env vars required — see below)

2. Backend :8000 + frontend :3000 running

3. `npx playwright install chromium` (once, from `frontend/`)



**PowerShell:**



```powershell

$env:PW_SKIP_WEB_SERVER='1'

npm run test:e2e:workintake-finish

```



**Bash / WSL:**



```bash

PW_SKIP_WEB_SERVER=1 npm run test:e2e:workintake-finish

```



### E2E seed (manual — env vars required)



Helper scripts (`dev:backend`, `dev:stack`, `test:backend`) **inject** env into their process. The seed script reads `DATABASE_URL` from the environment — set explicitly when seeding manually:



```powershell

$env:APP_ENV='development'

$env:ENVIRONMENT='development'

$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'

$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'

cd backend

.\.venv\Scripts\python.exe scripts\seed_commercial_e2e_fixture.py

```



Replace the path with your checkout location.



### Windows full stack



```powershell

.\scripts\dev.ps1

# or (same stack, invoked by dev.ps1)

.\scripts\start-dev.ps1

```



### Bash / WSL



```bash

./start_app.sh

```



## 3. Environment and database facts



### `.env` loading



| How you start | Env source |

|---------------|------------|

| `dev:stack`, `dev:backend`, `test:backend` | PowerShell helpers set vars |

| Manual uvicorn | Shell vars required; `backend/.env` is **not** auto-loaded |

| `python main.py` debug | May load repo root `.env` only |



`backend/.env.example` is a reference — copying to `backend/.env` does not help normal uvicorn unless you load it yourself.



### Local SQLite / migrations



- Dev boot uses **`Base.metadata.create_all`** — no migration step for basic local start.

- Alembic under `backend/alembic/` is for staged schema evolution — follow migration docs in dedicated builds only.

- Do not invent migration steps.



## 4. WorkOS protected areas



Treat these as **high-risk** without an explicit build and QA doc:



| Area | Location (typical) | Risk |

|------|-------------------|------|

| **CostEngine** | `backend/` cost engine services, formula handlers | Pricing correctness, production costing |

| **Pricing** | quote orchestration, markup policies, rate basis | Commercial totals, gate semantics |

| **Inventory** | inventory routers, sheet export, deductions | Stock truth; not a quote price source |

| **Status lifecycle** | quote/order status transitions | Irreversible workflow bugs |

| **Snapshots** | execution plans, output snapshots | Production handoff integrity |

| **WorkIntake V1** | legacy intake routes and persistence | Parallel path; don’t break during V2 work |

| **QuoteWizard handoff** | readiness → quote creation, `quote_input` | Operator blocking regressions |

| **ProductSystem templates** | template registry, dossier, activation scope | Wrong template activation |



## 5. Build discipline



For non-trivial work:



1. State **scope** and **boundary** up front (what you will not touch).

2. Add or update **`docs/qa/BUILD_<NAME>.md`** for significant builds.

3. Report **files changed** and **commands run** in your summary.

4. **Never declare PASS** without running tests appropriate to the change.

5. **Never declare `validate:frontend` green** until TS debt is resolved.

6. Document env/fixture steps when E2E or DB seed is required.

7. For page finalization and docs impact, follow **`docs/architecture/WORKOS_PAGE_COMPLETION_FOUNDATION.md`** (DoD, Figma policy, Documentation Impact Gate, Romanian-first, status vocabularies). Terminology: **`docs/architecture/WORKOS_UI_TERMINOLOGY_REGISTRY.md`**. Truth metadata schemas: **`docs/architecture/WORKOS_TRUTH_METADATA_CONTRACT.md`**. Do not declare a page `FINAL` without owner verification per that foundation.



QA doc template: purpose, context, files changed, commands + results, boundary, next steps.



## 6. Current architecture facts



- **WorkIntake V2** uses `WorkIntakeTemplateConfig` (`frontend/src/lib/workIntakeV2/templateConfig/`).

- **`TPL-VOLUMETRIC-LETTERS`** is the only fully wired V2 template implementation.

- **RAL / Oracal registry** is frontend config (`frontend/src/lib/colorRegistry/`), not automatic backend pricing.

- **QuoteWizard** shows volumetric finish display via `VolumetricFinishDisplayPanel` / `quote-finish-display`.

- **E2E finish smoke** exists: `frontend/e2e/work-intake-v2-to-quote-finish-display.spec.ts` (`test:e2e:workintake-finish`).

- **`TPL-ACM-CASSETTED-PANEL`** is future scope — seeds may exist; operator activation is out of bounds unless tasked.



Primary operator route for volumetric: `/intake-v2/:id`.



## 7. Do not do



- **Do not** partially activate ACM in WorkIntake V2 or QuoteWizard without a dedicated build.

- **Do not** wire RAL/Oracal registry entries into automatic Pricing/CostEngine rates.

- **Do not** modify CostEngine without a dedicated build and regression tests.

- **Do not** use Inventory as the direct price source for quotes.

- **Do not** delete files without a zero-import / reference check.

- **Do not** rewrite WorkIntake V2 shell, zones, or handoff without a documented reason.

- **Do not** change DB schemas or migrations unless explicitly in scope.

- **Do not** “fix” tests by weakening assertions to greenwash failures.

- **Do not** claim `validate:frontend` or full test suites are green without evidence.



## Repo map (quick)



```txt

backend/main.py          FastAPI entry

backend/tests/           pytest suite

backend/scripts/         seed and maintenance scripts

scripts/_workos-python.ps1   shared Python resolution

frontend/src/components/workos/   operator UI

frontend/e2e/            Playwright specs

docs/qa/                 build logs — read before overlapping work

```



Root human overview: [`README.md`](README.md).


