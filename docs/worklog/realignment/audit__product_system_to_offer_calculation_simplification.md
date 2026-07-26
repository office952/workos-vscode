# Audit: Product System → calcul ofertă (simplificare fără schimbare de formule)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Type** | READ-ONLY audit (logică + pricing ownership + UI + simplificare) |
| **Repo** | `C:\w\psiso` (`office952/workos-vscode`) — WorkOS real confirmat |
| **Scope** | Product System → ProductDefinition → ProductAggregate → CPP / EIC → Quote Snapshot V2 / Intake V6 offer |
| **Writes** | Doar acest raport + `docs/worklog/realignment/audit_assets/*` |
| **Forbidden** | Cod funcțional, formule, pricing rules, migrări, seed/reset, materialize, cleanup legacy, SVG/DWG parse |

---

## 1. Verdict scurt

| Metric | Value |
|--------|-------|
| **Verdict** | **PASS_WITH_WARNINGS** |
| **Cat suntem in directia stabilita** | **72/100%** |
| **Greutate sistem** | **78/100** (100 = foarte greu / fragil) |
| **Risc de crapare la extindere produse** | **81/100** |

### De ce acest verdict

**În direcție (ce ține):**

- Autoritatea comercială client activă este **Intake V6 → CommercialPriceProposal 7G → dry-run → priced-quote/write → Snapshot V2**.
- Legacy `POST /api/v1/entities/quotes/price` este **410** la runtime (verificat).
- ProductDefinition și ProductAggregate **nu calculează pret** în codul canonic (PD = compile; Aggregate = read model tehnic).
- CPP și EIC sunt separate conceptual; CPP blochează baza orară comercială.
- Quote Snapshot V2 composează 7G+7H fără CostEngine / QuoteOrchestrator.

**Warnings (ce trage scorul în jos):**

1. **UI greoi + surse de bani amestecate** pe operator (Intake „Rezultat comercial” + cost intern + provisional; Product System „Laboratory Closure” cu EIC+CPP pe overview; Quotes încă „+ Ofertă nouă”).
2. **Extensibilitate hard-coded**: `RULES_BY_TEMPLATE` / `SUPPORTED_TEMPLATES` doar pentru Letters v2 + ACM boxed; mini-module maps per template.
3. **Fail-open**: `illuminated` default-true; Product Truth pin cu `except: pass`.
4. **Dual SoT reguli**: `commercial_rules_volumetric_v2.py` (DEV_BRIDGE unit prices) vs Pricing Registry 7I încă incomplet.
5. **Dual cost intern**: EIC vs material_breakdown diagnostic în dry-run.
6. **Docs stale**: `21_WORKOS_IMPLEMENTATION_ROUTE.md` și docs 05/06 încă descriu 7G ca preview-only / `/price` ca path „today” — **contrazise de cod + runtime**.
7. **Runtime gap**: pe stack-ul live, EIC/Snapshot preview au returnat `*_not_found` chiar cu `workspace_id`, în timp ce CPP + cost-BOM + PD au mers — fragilitate / drift de runtime de marcat, nu reparat aici.
8. **Dry-run HTTP neexecutat** intenționat: `get_default_vat_pct` → `get_or_create` poate scrie în DB.

### Recomandare executivă (1 frază)

**Păstrați modularitatea 7G/7H/Snapshot; simplificați întâi UI-ul (ofertă vs intern vs lab) și modelul mental Product Template → Modules egale (fără „Module Template” / „Component Template” ca ierarhii separate); blocați vizual legacy QuoteWizard; nu atingeți formulele / coloanele `module_template_*` / freeze până la owner GO pe Nivel 2+.**

---

## 2. Harta fluxului real

### 2.1 Traseu canonic (cod + runtime evidence)

```text
Intake V6 workspace (payload + form contract / mini-modules)
        │
        ▼
ProductAggregateService.build[/for_workspace]
  (componente, materiale, ops, task_contract.task_rules)
        │
        ▼
ProductDefinitionBuilderService.build_preview
  (activare module, canonical values — NO price)
        │
        ├──────────────► CommercialPriceProposalService (7G)
        │                  commercial_rules_volumetric_v2 (+ registry rates)
        │                         │
        └──────────────► EstimatedInternalCostService (7H)
                           AggregateCostBom + internal_cost_rules + inventory
                                  │
Intake V6 priced-quote-dry-run ───┤  official totals = 7G + VAT
  (diagnostic: EIC / material_breakdown / cost-plus)
        │
        ▼
POST priced-quote/write  (operator confirm — WRITE; not exercised in audit)
        │
        ▼
Quote Snapshot V2 freeze (7G + 7H side-by-side; no /price)
        │
        ▼
Order Snapshot V2 → ExecutionPlan V2 (out of pricing authority; frozen only)
```

### 2.2 Runtime verification matrix (2026-07-23)

| Call | Result | Notes |
|------|--------|-------|
| `GET /api/v1/system/health` | 200 | Stack live :8000 / FE :3000 |
| `GET …/product-definition/TPL-VOLUMETRIC-LETTERS_v2` | 200 | PD compile OK |
| `GET …/aggregate/TPL-VOLUMETRIC-LETTERS_v2` | 200 | 5 components; `task_rules`=19 |
| `GET …/cost-bom-preview/…?workspace_id=` | 200 | BOM OK |
| `GET …/templates/…/pricing` | 200 | Recipe projection |
| `GET …/pricing/registry?template_code=` | 200 | Registry hub |
| `GET …/e2e-readiness/…/static` | 200 | Lab readiness |
| `POST …/commercial-price-preview/…` + workspace | **200 `ready`**, subtotal **1223.0054 RON**, 5 lines | Code-verified non-persist |
| `POST …/commercial-price-preview/…` fără workspace | 200 `blocked` | Expected |
| `POST …/estimated-internal-cost-preview/…` | **404 `estimated_internal_cost_preview_not_found`** | Route exists; service returned None — **runtime gap** |
| `POST …/quote-snapshot-v2/preview/…` | **404 `quote_snapshot_v2_preview_not_found`** | Likely blocked by EIC/compose — **runtime gap** |
| `POST …/templates/…/price-breakdown` | 200 | Adapter RO; ownership note EIC-first lab |
| `POST …/entities/quotes/price` | **410** | Retired confirmed |
| `GET …/priced-quote-dry-run` | **not executed — persistence risk** | `get_default_vat_pct` → `get_or_create` may write |
| `POST …/quote-snapshot-v2/freeze/…` | **not executed** | Persist path |
| `POST …/simulate-cost` | **not executed** | Legacy parallel (label only) |
| `POST /api/admin/productsystem/pricing-preview` | **not executed** | Admin material markup; out of offer path |

### 2.3 Preview POST safety gate

| Endpoint | Persist in code? | Executed? |
|----------|------------------|-----------|
| CPP preview | No (`No persist…`) + service fără `db.add/commit` | **Yes** |
| EIC preview | No (doc) | **Yes** (returned not_found) |
| Snapshot **preview** | `build_preview` only; persist doar în `freeze` | **Yes** (returned not_found) |
| Snapshot **freeze** | **Writes** (`_persist_snapshot`) | **No** |
| Price breakdown | Doc: does not persist | **Yes** |
| Intake dry-run GET | **Risk**: VAT/FX via `get_or_create` | **not executed — persistence risk** |
| simulate-cost | Claims `persisted=false` but CE+Orchestrator | **No** (legacy label) |

### 2.4 UI surfaces (live)

| Route | Observed |
|-------|----------|
| `/product-system/products/:templateCode` | Catalog admin + tabs (Prețuri / E2E / Publicare) + **Laboratory Closure** cu EIC+CPP pe overview |
| `/inventory/pricing` | Pricing Registry; „În calcul ofertă”; rate lipsă blochează calcul preliminar |
| `/intake-v6/:id/operator` | Operator path; **Rezultat comercial** + **Cost intern (referință)** pe același ecran |
| `/quotes` | Listă oferte V6 + CTA **„+ Ofertă nouă”**; banner menționează încă ProductSystem/**CostEngine** |

Screenshot paths: §6.

---

## 3. Ownership audit

| Componentă | Ce ar trebui să dețină | Ce deține azi | Deviație | Severitate | Recomandare |
|------------|------------------------|---------------|----------|------------|-------------|
| **ProductDefinition** | Produs concret, activări, canonical values; **nu pret** | Compile read-only; fail-open illuminated; Product Truth swallow | Ownership OK pe preț; honesty gates slabe | **HIGH** (gates) | Fail-closed illuminated + Product Truth (Nivel 2 GO) |
| **ProductAggregate** | Read model tehnic: components/materials/ops/`task_rules` | Da; workspace composition; dossier nu e BOM authority | Hard-coded mini-module maps | **MED** | Păstrează; template-onboarding playbook |
| **CommercialPriceProposal (7G)** | Propunere comercială client | **Autoritate runtime V6** | Reguli încă în fișier local + DEV_BRIDGE | **MED** | Keep; 7I migration later (GO) |
| **EstimatedInternalCost (7H)** | Estimare internă; nu ofertă client | Preview + snapshot side-B; diagnostic în dry-run | Runtime preview not_found pe stack live; dual vs material_breakdown | **HIGH** (runtime gap) | Investigare read-only dedicată; nu schimba formule |
| **Quote Snapshot V2** | Freeze 7G+7H la momentul ofertei | Compose + freeze paths; V6 poate freeze cu 7H partial | Preview not_found pe stack fără path clar | **MED** | Keep freeze point; nu recalcula din registry live |
| **Intake V6 dry-run/write** | Operator offer path | Official = 7G+VAT; write setează totals | Diagnostic cost-plus + dual internal traces | **MED** | Keep; UI trebuie să ascundă diagnostic |
| **Pricing Registry** | Cataloage separate (material / commercial / internal / capacity / analytics) | Hub UI încă amestecă „în calcul ofertă”; 7I incomplete | Amestec conceptual | **MED** | Label/classify (Nivel 1); nu hub unic |
| **CostEngine** | Doar cost intern legacy / sim | Încă în tree; folosit de simulate-cost + QuoteWizard sim | Poate arăta ca ofertă | **HIGH** (UI) | Freeze client path; label legacy |
| **QuoteOrchestrator** | Nu trebuie să dețină pret client | Cost-plus pe CE; retired pe `/price` | Cod viu pentru sim | **MED** | Keep blocked; future cleanup Step 12 |
| **Legacy `/price`** | Mort | HTTP 410 | Docs încă „DEAD_LEGACY_RISK callable” | **LOW** (dacă 410 ține) | Keep blocked |
| **ExecutionPlan** | Citește doar frozen Order Snapshot V2 | Out of pricing audit; conceptual OK | — | — | Nu lega de `/price` / live Intake |
| **HR / Pontaj / rate_per_hour** | Capacity / internal — **nu tarif client** | WC `rate_per_hour` încă în registry UI ca „pricing” | Confuzie etichetă | **MED** | Relabel capacity (Nivel 1) |

---

## 4. Functionalitate audit

### Ce merge

- PD + Aggregate compile pentru `TPL-VOLUMETRIC-LETTERS_v2` (runtime GET).
- CPP preview cu workspace → `ready` + total comercial.
- Cost-BOM preview.
- Pricing Registry + template pricing recipe GET.
- Legacy `/price` → 410.
- Intake V6 UI operator (config + confirm flow) pe workspace live.
- Quotes listă pe spine V6 (oferte acceptate vizibile).

### Ce este partial

- EIC / Snapshot V2 preview pe runtime live (404 not_found cu workspace) — **gap**.
- Pricing Registry 7I (separare tipuri) — documentat, nu închis.
- Form contract / mini-modules — pilot-heavy (Letters + ACM forks).
- E2E readiness / publication — lab gates, nu autoritate ofertă.
- Docs 05/06/21 — stale față de runtime V6+7G.

### Ce este preview-only

- Product-system CPP/EIC/Snapshot **preview** endpoints.
- Price breakdown adapter.
- AcmPanel provisional pricing (Intake).
- Face/Back prep cost draft.
- Cost-plus diagnostic în dry-run (`diagnostic_only=True`).
- Product System Reference Complete / Finish Line (laboratory closure).

### Ce este legacy / dead risk

- `POST …/quotes/price` (retired 410 — keep).
- QuoteOrchestrator + CostEngine ca path comercial.
- `POST …/simulate-cost`.
- Admin `POST /api/admin/productsystem/pricing-preview`.
- QuoteWizard „Ofertă nouă” + CostEngine simulare preliminară.
- Deep-link `LEGACY_QUOTE_PRICE_INTAKE_V6_HREF = "/intake-v6"` (ruta reală e `/intake-v6/operator`).

### Ce este blocat corect

- `/price` 410.
- CPP forbidden hourly commercial tokens.
- Snapshot V6 fără synthetic CPP reconstruction.
- Materialize / ExecutionTasks — out of scope; remain owner-GO.

### Ce este periculos dacă rămâne așa

*1. Illuminated fail-open* — LED poate intra comercial fără confirmare explicită.  
*2. Product Truth `except: pass`* — pricing pe draft nepin-uit.  
*3. UI „ofertă” pe multiple ecrane* — operator poate cita EIC / provisional / CostEngine sim.  
*4. DEV_BRIDGE unit prices în regulile comerciale* — prețuri hardcodate în 7G.  
*5. Extindere produs nou fără maps* — CPP/EIC/Snapshot returnează None / dry-run blocked.  
*6. EIC runtime not_found* — Snapshot dual path fragil pe stack-ul observat.

---

## 5. Pricing / formula audit

### Unde sunt formulele comerciale (client)

| Locație | Rol |
|---------|-----|
| `backend/data/commercial_rules_volumetric_v2.py` | Reguli ml/m2/buc + **DEV_BRIDGE_*** unit prices |
| `backend/services/commercial_price_proposal_service.py` | Aplicare reguli, qty, registry bind, anti-hourly |
| `backend/services/linked_logo_commercial_price_service.py` | Linii logo; FX fail-closed (fără bootstrap write) |
| Pricing Registry op rates (când `registry_pricing_code`) | Rate comerciale mapate |
| Company VAT settings | TVA pe dry-run oficial (via `get_default_vat_pct`) |

### Unde sunt costurile interne

| Locație | Rol |
|---------|-----|
| `backend/data/internal_cost_rules_volumetric_v2.py` | Reguli EIC |
| `backend/services/estimated_internal_cost_service.py` | Builder 7H; WC hourly **exclus** din totals |
| `backend/services/aggregate_cost_bom_adapter.py` | BOM costabil |
| Inventory `unit_cost` | Achiziție materiale |
| `cost_engine_service.py` | Legacy calc (labour/machine hourly profiles) |

### Materiale

- Material market registry + inventory unit costs.
- Pricing Registry tab „Prețuri materiale (cost achiziție)”.
- EIC consumă inventory; CPP nu trebuie să fie cost-plus pe material (exceptând reguli comerciale explicite).

### Capacity / time / rates

- WC `rate_per_hour` în registry — **capacity / internal**, nu tarif client.
- EIC `capacity_hints` — minute, excluse din totals.
- CostEngine `_OVERHEAD_PROFILES` labour 80 / machine 40 — **nu** pe path V6 oficial.
- HR / Pontaj — **în afara** acestui audit; nu trebuie să intre în pret client.

### Ce nu trebuie confundat cu pret client

- EIC totals / material_breakdown / diagnostic cost-plus
- CostEngine simulate-cost response (chiar dacă `persisted=false`)
- Admin material markup preview
- Pricing Registry „preț net estimat” (cost + markup orientativ)
- Product System Laboratory Closure EIC/CPP chips
- QuoteWizard CostEngine „simulare preliminară”

### Ce trebuie separat în UI/API

| Layer | API / UI label țintă |
|-------|----------------------|
| Commercial client | „Preț ofertă (7G)” / official după write |
| Internal estimate | „Cost intern (EIC) — intern” |
| Materials purchase | „Cost achiziție” |
| Capacity | „Efort / capacitate — nu tarif client” |
| Lab calibration | „Laborator / admin — nu ofertă” |
| Legacy | „Retras / simulare internă” |

---

## 6. Parallel pricing paths (comparație obligatorie)

| Path | Canonic / legacy? | Influențează pret final client? | Scrie / citește? | PD/Aggregate sau ocolește? | Risc dublare | Recomandare |
|------|-------------------|---------------------------------|------------------|----------------------------|--------------|-------------|
| **Legacy `/price`** | Legacy retired | **Nu** (410) | Nu calculează / nu scrie | N/A | Low dacă rămâne 410 | **block** (keep 410) |
| **QuoteOrchestrator** | Legacy glue | Nu pe path retired; da dacă reînviat | In-memory; write doar dacă caller persistă | Classic PD + CostEngine | **High** vs 7G | **freeze** + **label legacy** |
| **CostEngine** | Legacy calculator | Indirect dacă Orchestrator/sim e citit ca ofertă | Calculator RO | Classic PD layers | **High** vs EIC | **freeze** for client; evolve under 7H only |
| **CommercialPriceProposal** | **Canonical commercial** | **Da** (subtotal autoritate) | Preview RO; write via V6 | PD + Aggregate measurements | Med (temp rules file) | **keep** |
| **EstimatedInternalCost** | **Canonical internal** | Nu (margin confidence) | Preview RO | PD + Cost BOM | Med vs CE / material_breakdown | **keep** (fix runtime gap) |
| **Quote Snapshot V2** | **Canonical freeze** | Da după freeze/handoff | Preview RO; freeze writes | Via 7G+7H | Low | **keep** |
| **Intake V6 priced-quote dry-run** | **Canonical operator path** | **Da** (official 7G+VAT); write setează grand_total | Dry-run: risk VAT bootstrap write; write = persist | Via CPP/EIC | Med (diagnostics) | **keep**; guard diagnostics in UI |
| **Product price breakdown** | Adapter / lab read-model | Nu (nu recalculează) | RO | Via CPP+EIC | Low (display) | **keep**; label lab |
| **Admin pricing preview** | Legacy/admin material tool | Nu | RO (`no_write_guarantee`) | **Ocolește** PD/Aggregate | High confusion | **label legacy** / admin-only |
| **simulate-cost** | Legacy simulation | Poate *arăta* ca preț client | RO `persisted=false` | Orchestrator/CE | **Very high** | **label legacy**; **block** as offer authority |

---

## 7. UI audit (severity + sincer)

### Scor UI: greoi, confuz, periculos operațional dacă e lăsat așa

### Screenshot assets

| File | Surface |
|------|---------|
| [`audit_assets/01_product_system_backend_compat_gate.png`](./audit_assets/01_product_system_backend_compat_gate.png) | Gate / shell (runtime pairing) |
| [`audit_assets/02_quotes_page.png`](./audit_assets/02_quotes_page.png) | `/quotes` — „+ Ofertă nouă” + banner CostEngine |
| [`audit_assets/04_pricing_registry.png`](./audit_assets/04_pricing_registry.png) | `/inventory/pricing` — „În calcul ofertă” / rate lipsă |
| [`audit_assets/05_product_system_catalog.png`](./audit_assets/05_product_system_catalog.png) | `/product-system` — Laboratory Closure EIC+CPP |
| [`audit_assets/06_intake_v6_operator_commercial.png`](./audit_assets/06_intake_v6_operator_commercial.png) | Intake V6 — Rezultat comercial + cost intern |

### Per rută

#### `/product-system/products` (+ detail)

- **Vede:** catalog admin, multe tab-uri (Prezentare → Prețuri → E2E → Publicare → Runtime), Laboratory Closure cu **EIC + CPP** pe overview.
- **Prea greu pentru operator?** **DA**
- **Prea tehnic?** **DA** (template codes, publication, E2E)
- **Mută la admin-only?** **DA** (întreg Product System)
- **Pare oficial dar e preview?** **DA** — Reference Complete / Pricing Studio
- **Poate induce în eroare oferta?** **DA** — chips EIC/CPP lângă PASS
- **Grupare / redenumire / ascundere:** Overview = identitate + lifecycle; Prețuri → „Rețetă tarifară (admin)”; E2E/Reference Complete sub Advanced; hide Laboratory Closure din default overview.

#### `/inventory/pricing`

- **Vede:** registry materiale/ops, „În calcul ofertă”, rate lipsă, adaos.
- **Prea greu operator?** **DA** (zilnic); **NU** pentru pricing admin
- **Admin-only?** **DA** pentru edituri
- **Preview vs oficial?** „Preț net estimat” / coverage = **nu** e 7G client total
- **Acțiune:** redenumire nav „Tarife & adaos (admin)”; etichetă „Nu este preț ofertă”.

#### `/intake-v6/:workspaceId/operator`

- **Vede:** config produs + **Rezultat comercial** + **Cost intern (referință)** + ajustări + blockers.
- **Prea greu?** **DA** — multe suprafețe de bani
- **Mislead?** **HIGH** — titlu „Rezultat comercial” în timp ce prețul client poate fi încă blocat; cost intern vizibil ca hero secundar; provisional AcmPanel pe alte workspace-uri
- **Acțiune:** un singur hero: „Preț ofertă oficial / neprețuit”; cost intern într-un drawer „Intern (admin/owner)”; diagnostics lazy.

#### `/quotes` + QuoteWizard

- **Vede:** oferte V6 + CTA **„+ Ofertă nouă”**; banner menționează CostEngine.
- **Mislead?** **HIGH** — CTA sugerează path comercial activ; Wizard + CostEngine sim încă există
- **Bug link:** `/intake-v6` ≠ `/intake-v6/operator`
- **Acțiune:** CTA → „Deschide Intake V6”; wizard lab-flag sau ascuns; fix deep-link.

### Opinie sinceră

UI-ul **nu e „urât” — e supraîncărcat de adevăruri paralele**. Operatorul vede prea multe numere care arată ca ofertă. Adminul vede același amestec fără stratificare clară. Product System arată ca laborator + catalog + pricing studio într-un singur loc. Asta crește greutatea percepției peste greutatea reală a formulelor.

---

## 8. Simplification map (fără schimbare formule)

Constrângeri respectate: PD ≠ pret; Aggregate ≠ ofertă; Registry ≠ hub amestecat; HR/Pontaj ≠ pret client; ExecutionPlan ← frozen Order Snapshot; Snapshot V2 = freeze point; formule neschimbate.

### Nivel 1 — safe, fără schimbări funcționale (primul)

| Ce simplifică | Ce păstrează | Risc redus | Fișiere viitoare | Teste |
|---------------|--------------|------------|------------------|-------|
| Etichete UI: oficial vs preview vs intern vs lab | Toate calculele | Confuzie operator | Intake commercial panels, ProductSystem overview, Pricing.tsx, Quotes.tsx | Vitest copy/authority labels |
| Un singur hero de bani pe Intake | 7G authority | Citare greșită | `IntakeV6LiveCalculationSummary`, Review step | Component tests |
| Ascunde/lab-flag QuoteWizard CTA | Backend 410 | Path mort vizibil | `Quotes.tsx`, `legacyQuotePriceRetirement.ts` | Route/CTA tests |
| Fix link `/intake-v6` → `/intake-v6/operator` | — | Dead-end | `legacyQuotePriceRetirement.ts` | Unit |
| Relabel WC rate „capacity / internal” | Rate values | Confuzie tarif | Pricing registry UI copy | Snapshot copy |
| Collapse Product System planned tabs + hide Reference Complete default | Lab data | Noise | `productSystemShellConfig`, TemplateDetail | UI tests |
| **UI naming: „Module Template” / „Component Template” → „Module produs / Module tehnice”** (egal față/cant/spate) | Backend `module_template_*`, link rows, formule | Ierarhie mentală falsă | `ProductSystem.tsx`, `productSystemCanonicalModel.ts`, `TemplateLibraryView.tsx`, ownership panels | Copy/snapshot tests — **DONE 2026-07-23** ([worklog](./2026-07-23_product_template_modules_nivel1_labels.md)) |

### Nivel 2 — risc mediu, necesita GO

| Ce simplifică | Ce păstrează | Risc redus | Fișiere | Teste |
|---------------|--------------|------------|---------|-------|
| Fail-closed `illuminated` + Product Truth pin | Formule | LED / draft greșit | `product_definition_builder_service.py` | PD unit + V6 readiness |
| Unificare readiness display (un aggregator UI peste aceleași gates) | Gate logic backend | Multi-readiness | Intake readiness libs + PS panels | Contract tests |
| Separare UI Registry pe tipuri (material / commercial / internal / capacity) fără muta formule | Rate values | Hub amestecat | Pricing page + API projections | Registry FE tests |
| Investigare + reparare EIC preview not_found (dacă e bug runtime) | Formule EIC | Snapshot dual | EIC + cost BOM services | pytest EIC/Snapshot |
| Dry-run VAT/FX read fără `get_or_create` write | VAT rate semantics | Side-effect pe GET | `company_commercial_settings_service` + dry-run | pytest no-write |
| **Model mental în docs/API display: Product Template compune Modules egale; depreciază vocabularul Component Template ca entitate separată** (fără rename DB) | Link edges + child PT rows | Dual-vocabulary debt | availability labels, component-contract views, glossary FE/BE | Contract + availability tests |

### Nivel 3 — arhitectură, decizie owner

| Ce simplifică | Ce păstrează | Risc redus | Fișiere | Teste |
|---------------|--------------|------------|---------|-------|
| Pricing Registry 7I: mută DEV_BRIDGE → registry comercial clasificat | Formule/ml/m2/buc | Dual SoT rules | `commercial_rules_*`, registry services | Golden commercial fixtures |
| Template onboarding fără hard-coded `RULES_BY_TEMPLATE` maps (dar aceleași formule) | Modularitate | Extensie produse | CPP/EIC catalogs, form contracts | New-template checklist |
| Step 12 cleanup: QuoteOrchestrator/simulate-cost/admin preview | 410 + V6 | Parallel paths | routers/services legacy | Isolation tests |
| Role gates: Product System + Pricing edit admin-only | Operator Intake | Operator in lab | App nav + permissions | Authz tests |
| **Curățare ierarhie: rename controlat `module_template_*` → `module_*` / unificare Component Template campaign cu Modules egale; clarificare mini-module vs module** | Formule, 7G/7H, Snapshot freeze | Nested-template confusion | models/links, seeds, Intake fields, Aggregate maps | E2E Letters + Aggregate + CPP/EIC |

---

## 8A. Product Template → Modules Simplification

### Verdict scurt pe model mental

| Întrebare | Răspuns |
|-----------|---------|
| **Păstrăm sau eliminăm „Module Template” ca concept?** | **Eliminăm din vocabularul operator/admin (Nivel 1).** În storage, copilul rămâne un **Product Template** legat prin `product_template_module_links` — nu inventăm un tip nou. Termenul UI țintă: **Module** (module produs / module tehnice). |
| **Există tabel `ComponentTemplate` / `ModuleTemplate`?** | **Nu.** Un singur tip persistat: `product_templates`. „Component Template” = concept UI/docs (`STORAGE_MIXED`). „Module Template” = coloane/API pe link (`module_template_code`) = child Product Template. |
| **Față / cant / spate sunt egale?** | **Da la composition** (peer links). Asimetriile sunt **dependențe de proces** (ex. cant depinde de perimetru față) și mapări mini-module — nu ierarhie nested FACE→CANT→BACK. |

### Modelul actual găsit în cod

```text
product_templates  (UN singur tip de rând)
   │
   ├─ root_offerable     ex. TPL-VOLUMETRIC-LETTERS_v2   = Product Template comercial
   ├─ component_only     ex. FACE / BACK / ALUMINIU / LED / FINISH
   └─ dual-role          ex. premount / ACM boxed
         │
         └── product_template_module_links
               module_template_id / module_template_code  → child Product Template
               relation_type, trigger_field, usage_mode, instance_schema_id

Paralel (nu tabel CT):
  Mini-module registry  (debitare_fata, modelare_cant, debitare_spate, …)
  ProductAggregate.modules  (required/optional compiled from links)
  UI vocabulary: "Component Template", "Module Template", "Module produs"
```

Evidențe cheie:

- Link model: `backend/models/product_template_module_links.py` — coloane `module_template_*`; comentariu explicit „no CT table”.
- Contract view: `no_component_templates_table=True` în `product_template_component_contract_service.py` / schema.
- Aggregate map: `CHILD_TEMPLATE_MINI_MODULE` în `product_aggregate_service.py` (child TPL → mini-module code).
- Role metadata (prezentare, nu ierarhie): `ROLE_METADATA_BY_MODULE_CODE` în `product_template_availability_service.py`.
- FE dictionary: `frontend/src/lib/productSystemCanonicalModel.ts` — Component Template = `CONCEPT_CANONICAL — STORAGE_MIXED`.
- UI greu: `ProductSystem.tsx` — „Product Template composes; Component Template owns truth”, „backing module templates”, „1 Product Composer + 6 Component Templates”.
- Workflow-ADV: `docs/workflow-adv/TERMINOLOGY.md` — Product Template canonic; **nu** crea `ComponentTemplate` paralel fără nevoie dovedită.

### Inventar: unde apare ce (necesar vs simplificabil)

| Concept / string | Unde | Necesar sau → „Module”? | Naming/UI vs backend | Fișiere afectate la schimbare | Risc formule | Risc Aggregate/CPP/EIC | Nivel 1 safe (label)? | Nivel 2+ GO? |
|------------------|------|-------------------------|----------------------|-------------------------------|--------------|------------------------|-----------------------|--------------|
| **Module Template** (`module_template_code`) | DB links, seeds, Intake fields (`face_module_template_code`, `volum_aluminum_module_template_code`, …), Aggregate | Backend: **necesar ca pointer** la child PT. Vocabular: → **Module** | **Backend real** (coloane + JSON) | models/links, seeds, Intake V6, PD payload, tests, QA fixtures | **High** dacă se redenumesc câmpuri fără migrare | **High** pe trigger/active modules | **Da** — UI „Module” / „Modul tehnic” | Rename coloane/fields = Nivel 3 |
| **Component Template** | FE ProductSystem ownership panels, canonical model, worklogs | **Nu ca tip separat** — e child PT. → **Module** | **Aproape doar UI/docs** | `ProductSystem.tsx`, `productSystemCanonicalModel.ts`, component-first panels, docs | **Low** (label) | **Low** dacă nu se schimbă linkuri | **Da — prioritar** | Doar dacă se încearcă tabel CT nou (**nu** recomandat) |
| **Product Module Template** | Occasional synonym | → **Module** sub Product Template | Naming | copy/docs | Low | Low | Da | — |
| **Template component** / `components_json` | BOM rows pe PT | Păstrează ca **BOM/component rows**, nu „template separat” | Backend JSON | template editors, Aggregate components[] | Med dacă se mută ownership | Med (BOM → EIC) | Label „componente BOM” vs „module” | Refactor ownership = Nivel 2/3 |
| **Nested template** | Child PT under parent via links | **Păstrează composition edge**; elimină *percepția* de sistem nested separat | Backend links + UI | availability, composition panels | Low dacă doar UI | Low | Da — „Module ale produsului” | Flatten storage = **nu** (distruge reuse) |
| **Role template** / role metadata | `ROLE_METADATA_BY_MODULE_CODE` | Role = **etichetă** (față/cant/spate…), nu tip | Backend map + UI | availability service, catalog | Low | Low | Da — role egale vizual | — |
| **Component path** / `instance_schema_id` | Link edge → payload paths | Necesar tehnic (binding Intake→modul) | Backend | module links, form contract | Med | Med (activare module) | Nu redenumi path-uri în Nivel 1 | Orice rename path = Nivel 2+ |
| **Mini-module** | Registry paralel (`debitare_fata`…) | **Păstrează** ca pachet operațional/comercial; **nu** confunda cu Module (child PT) | Backend data + PD/CPP | `mini_module_registry_*`, Aggregate, CPP active modules | **High** dacă se amestecă cu Module | **High** (CPP module activation) | Label clar: „Mini-modul operațional ≠ Modul produs” | Unificare prematură = Nivel 3, risc formule |
| **Module vs Component differentiation** | UI campaign „Component Template owns truth” | Diferențierea artificială **poate deveni** Module egale cu role | UI dominant | ProductSystem ownership copy | Low | Low | **Da** | — |

### Modelul țintă propus

```text
Product Template  (nivel comercial / configurabil — un singur tip rădăcină)
   └── Modules[]  (egale ca valoare structurală)
         față | cant/volum | spate | iluminare | structură | finisaj | montaj | accesorii…
         fiecare: materiale, operații, reguli, dependențe, readiness, contribuție CPP/EIC

Storage real (neschimbat în Nivel 1):
  Modules = child rows in product_templates + product_template_module_links
  Mini-modules = operational packaging registry (parallel, named distinctly)
```

Reguli țintă:

1. Product Template **compune** Modules — nu există al doilea sistem de „Module Templates”.
2. Față / cant / spate / iluminare / … sunt **module egale**; diferențele = role + dependențe de proces, nu clase de template.
3. Nu creăm tabel `ComponentTemplate`.
4. Mini-module rămâne concept **separat** (operațional), etichetat ca atare — nu „template”.

### Ce se poate redenumi fără risc (Nivel 1)

- Copy UI: „Component Template” → „Modul tehnic” / „Modul produs”.
- „Module Template” / „backing module templates” → „Module (legate)” / „Module tehnice”.
- „1 Product Composer + 6 Component Templates” → „1 Product Template + N Module egale”.
- Catalog: păstrează „Module produs” (`TemplateLibraryView`) ca limbaj principal.
- Glossary FE: marchează Component Template ca **deprecated label** → Module; status storage neschimbat.
- Intake: etichete operator pe selectoare — fără rename pe `*_module_template_code` fields.

### Ce necesită refactor (Nivel 2 / 3, owner GO)

| Schimbare | Nivel | De ce GO |
|-----------|-------|----------|
| API display DTOs: `display_name_ro: "Modul"` peste `module_template_code` | 2 | Contract FE/BE |
| Deprecare campaniei „move into Component Template” din ProductSystem panels | 2 | Schimbă teaching model |
| Rename DB/API `module_template_*` → `module_*` | **3** | Migrare + Intake payload + fixtures + snapshots |
| Unificare mini-module cu Module (child PT) într-un singur tip | **3 — nerecomandat prematur** | Risc direct pe CPP active modules / formule |
| Creare tabel `ComponentTemplate` | **Nu** | Contrazice Workflow-ADV + storage actual |

### Ce nu trebuie atins

- Formule CPP/EIC / `RULES_BY_TEMPLATE` / DEV_BRIDGE (în acest track).
- Pricing Registry separation.
- ProductDefinition ca non-price compiler.
- ProductAggregate ca read model (poate doar labels).
- Quote Snapshot V2 freeze semantics.
- Coloanele `module_template_*` și câmpurile Intake `*_module_template_code` **în Nivel 1**.
- Ștergerea child Product Templates (FACE/BACK/…) — sunt **Modulele** reale.
- Mini-module registry keys folosite de CPP (`debitare_fata`…).

### Impact pe straturi

| Strat | Impact Nivel 1 (label) | Impact Nivel 2/3 |
|-------|------------------------|------------------|
| **Intake V6** | Claritate pe selectoare module; fără rename JSON | Rename `*_module_template_code` = breaking pe payload / dry-run |
| **ProductDefinition** | Niciun; PD deja compilează activări | Path bindings trebuie migrate dacă se redenumesc trigger fields |
| **ProductAggregate** | Niciun pe calc; optional display | `CHILD_TEMPLATE_MINI_MODULE` + `modules.required/optional` rămân; rename codes = teste Aggregate |
| **CPP / EIC** | Niciun pe formule | Active modules / mini-module codes trebuie stabile; orice unificare greșită rupe linii |
| **Quote Snapshot V2** | Niciun | Freeze conține structuri existente — rename după freeze = incompatibilitate istorică → doar DEV versions |

### Recomandare clară

1. **Eliminați din UI/docs conceptul de „Module Template” ca ierarhie** — înlocuiți cu **Module** sub **Product Template**.
2. **Nu creați / nu „activați” Component Template ca tip de storage** — e deja child Product Template; campania UI care sugerează alt sistem trebuie oprită (Nivel 1).
3. **Păstrați composition-ul actual** (parent PT + links + child PTs) — e deja aproape de modelul țintă; greutatea e **vocabularul triplu** (Product / Component / Module Template + mini-module).
4. **Păstrați mini-module ca registry operațional separat**, cu etichetă clară — nu le „promovați” la Module Template și nu le ștergeți în Nivel 1/2.
5. **Față / cant / spate**: tratați-le egal în UI; păstrați dependențele de proces în backend fără a le vinde ca nested templates.

---

## 9. Răspunsuri la întrebările principale

1. **Traseu real?** Intake V6 → PD/Aggregate → **CPP 7G** (oficial) + EIC 7H (intern) → dry-run → write → Snapshot V2.  
2. **Mai multe trasee pret?** Da: canonic 7G; legacy `/price`(410); Orchestrator/CE; simulate-cost; admin material preview; diagnostics cost-plus.  
3. **Unde e prea greu?** UI (PS + Intake money + Quotes CTA + Registry); hard-coded template maps; dual readiness.  
4. **Logică duplicată?** Reguli comerciale file vs registry; EIC vs material_breakdown; CE vs EIC; preview PS vs dry-run V6.  
5. **Amestec truths?** Product Truth (PD/Intake) vs Cost (EIC/CE) vs Commercial (7G) vs Execution (frozen plan) — cele mai greșite amestecuri sunt în **UI**.  
6. **Crapă la produse noi?** Lipsă din `RULES_BY_TEMPLATE` / form contract / mini-module maps / Snapshot SUPPORTED_TEMPLATES / ACM special forks.  
7. **UI greșit poziționat?** Laboratory Closure, Pricing „în calcul ofertă”, Intake cost intern ca hero, Quotes „Ofertă nouă”.  
8. **Simplificăm fără formule?** Da — Nivel 1 labeling/CTA/grouping + **Product Template → Modules** naming; apoi Nivel 2 gates/readiness UI.  
9. **Păstrăm exact?** Separarea 7G/7H; Snapshot freeze; `/price` 410; PD fără pret; Aggregate tehnic; operator confirm pe write; child PT links + mini-module keys.  
10. **Blocăm până la GO?** Orice schimbare formule/DEV_BRIDGE→registry, fail-closed illuminated, cleanup legacy delete, materialize, ExecutionPlan writes, rename `module_template_*`, creare `ComponentTemplate`, unfreeze feature work.

---

## 10. Recomandare de abordare finală

### Păstrăm modularitatea cum?

Păstrați **patru cutii**: Product Truth (PD/Aggregate) → Commercial (7G) → Internal (7H) → Freeze (Snapshot V2). Nu unificați într-un singur engine opac.

### Simplificăm logica cum?

Nu prin rescriere formule. Prin: **un singur path vizibil de ofertă (Intake V6)**, etichetare strictă, reducerea locurilor unde UI decide „ce e oficial”, și (mai târziu) registry clasificat 7I.

### Păstrăm formulele cum?

Nicio editare pe `commercial_rules_*` / `internal_cost_rules_*` / CostEngine profiles în build-urile de simplificare UI. Orice migrare DEV_BRIDGE → registry = **owner GO** cu golden tests.

### Cum evităm să crape sistemul?

- Template onboarding checklist (form contract + rules + mini-module map + Snapshot support) înainte de produs nou.  
- Fail-closed pe Product Truth / illuminated.  
- Nu permiteți path-uri UI care arată CostEngine ca ofertă.  
- Un singur write comercial: V6 priced-quote/write.

### Ce facem cu legacy `/price`?

**Keep blocked (410).** Nu șterge încă (Step 12). Actualizați docs care încă zic „callable”.

### Ce facem cu Pricing Registry?

**Nu** hub unic. Stratificați UI: Material Prices / Commercial Rules / Internal Rules / Capacity / Analytics. Rate pe oră = capacity. Edit = admin.

### Ce facem cu UI Product System?

Tratați-l ca **admin/lab**. Scoateți Laboratory Closure și EIC/CPP hero de pe overview-ul default. „Prețuri template” = rețetă/calibare, nu ofertă. Înlocuiți „Component Template” / „Module Template” cu **Product Template → Modules egale** (față/cant/spate = module, nu sisteme nested).

### Ce simplificăm prima dată (fără logică)

1. Fix CTA Quotes + deep-link Intake V6.  
2. Un hero de bani pe Intake; cost intern în drawer.  
3. Relabel Product System / Pricing ca admin; hide lab chips.  
4. Copy „preview ≠ oficial”.  
5. **Naming Product Template → Modules** (fără rename `module_template_*`).

### Ce blocăm până la owner GO

- Schimbări formule / DEV_BRIDGE migration  
- Delete QuoteOrchestrator / CE / simulate-cost  
- Fail-closed illuminated / Product Truth (Nivel 2)  
- Freeze/write/materialize exercises  
- Feature expansion ACM/new products fără checklist  
- Rename DB/API `module_template_*` / unificare mini-module↔Module  
- Creare tabel `ComponentTemplate`  
- `CURRENT_WORKOS_REFERENCE_FREEZE_OFF` fără instrucțiune explicită

---

## 11. Dead pieces / parallel paths check (candidates only — NU șterge)

| Candidate | De ce | Acțiune propusă |
|-----------|-------|-----------------|
| `POST /entities/quotes/price` | Retired 410 | Keep block; Step 12 |
| `quote_orchestrator.py` | Cost-plus legacy | Label + freeze client |
| `cost_engine_service.py` hourly profiles | Parallel costing | Freeze client; retarget docs to 7H |
| `product_system_cost_simulation` | Sim arată comercial | Label legacy / hide UI |
| `admin_productsystem_pricing_preview` | Material markup ≠ 7G | Admin-only label |
| QuoteWizard create path | CTA încă activ vizual | Hide/lab-flag (Nivel 1) |
| Docs 05/06/21 stale claims | Spun 7G missing / `/price` today | Doc correction GO |
| Underscore routers `product_system` vs `product-system` | Parallel naming | Step 12 inventory |

---

## 12. Runtime gaps (exact ce nu s-a putut verifica)

| Item | Status |
|------|--------|
| Intake V6 `priced-quote-dry-run` HTTP | **not executed — persistence risk** (`get_or_create`) |
| Snapshot freeze / priced-quote write | **not executed** (write) |
| EIC preview success path pe stack live | **failed with not_found** (gap) |
| Snapshot preview success path | **failed with not_found** (gap) |
| FE↔BE local_compatibility | FE raportează BUILD_25 staging; `local_compatibility` 404 — pairing imperfect |
| DB SQL deep dive | Skip (nu necesar; API GET suficiente) |

---

## 13. Cat suntem in directia stabilita — scor detaliat

| Dimensiune | Scor | Note |
|------------|------|------|
| Canonical commercial authority (7G/V6) | 90 | Cod + `/price` 410 + CPP ready |
| Internal vs commercial separation (engine) | 80 | Separat în servicii; dual diagnostics |
| Snapshot freeze discipline | 75 | Design OK; preview runtime gap |
| Registry separation 7I | 45 | Docs da; UI/hub încă amestecat |
| UI honesty / stratification | 40 | Principalul drag |
| Extensibility for new products | 35 | Hard-coded maps |
| Docs freshness | 50 | 21/05/06 stale |
| Mental model Product Template → Modules | 55 | Storage deja aproape; vocabular triplu (CT/MT/mini) trage greutatea |
| **Weighted overall** | **72%** | |

---

## 14. Următorul prompt recomandat

```text
PLAN MODE ONLY FIRST. Nu implementa până la GO.

Context: audit PASS_WITH_WARNINGS livrat în
docs/worklog/realignment/audit__product_system_to_offer_calculation_simplification.md
(inclusiv secțiunea 8A Product Template → Modules Simplification).

Build țintă: Nivel 1 UI honesty / simplification ONLY (fără schimbare formule, fără pricing rules,
fără migrări, fără freeze/write/materialize, fără cleanup delete legacy, fără rename
module_template_* / mini-module codes).

Scope:
1) Quotes: înlocuiește CTA „Ofertă nouă” cu „Deschide Intake V6”; fix
   LEGACY_QUOTE_PRICE_INTAKE_V6_HREF → /intake-v6/operator; lab-flag sau hide QuoteWizard.
2) Intake V6: un singur hero de bani (oficial 7G / neprețuit); mută cost intern + diagnostics
   în drawer; păstrează authority commercial_price_proposal_7g.
3) Product System overview: ascunde/default-collapse Laboratory Closure EIC+CPP;
   redenumește „Prețuri template” → „Rețetă tarifară (admin)”.
4) Pricing Registry copy: „Nu este preț ofertă”; WC rate = capacity/internal.
5) Product Template → Modules naming ONLY:
   - UI/docs: „Component Template” / „Module Template” → „Module” / „Module tehnice”;
   - față / cant / spate / iluminare afișate ca module egale (nu nested template systems);
   - păstrează mini-module ca etichetă separată „Mini-modul operațional”;
   - NU redenumi coloane/fields module_template_*; NU crea ComponentTemplate table.

Out of scope: formule, DEV_BRIDGE migration, illuminated fail-closed, EIC not_found fix,
delete Orchestrator/CE, Snapshot freeze, materialize, DB renames.

Livrează planul cu fișiere concrete + teste Vitest țintite, apoi așteaptă GO.
```

Dacă owner vrea mai întâi gap-ul EIC runtime (înainte de UI):

```text
AUDIT READ-ONLY FOLLOW-UP: de ce POST estimated-internal-cost-preview și
quote-snapshot-v2/preview returnează not_found pe runtime live când
cost-bom-preview + CPP ready pentru același workspace_id.
Fără fix până la GO. Raport scurt în docs/worklog/realignment/.
```

---

## 15. Acceptance self-check

| Criteriu | Status |
|----------|--------|
| Audit read-only | **PASS** |
| Fără modificări cod funcțional | **PASS** |
| Fără migrări / seed / reset | **PASS** |
| Fără POST materialize / freeze / write | **PASS** |
| Fără schimbări pricing/formule | **PASS** |
| Raport persistent în `docs/worklog/realignment/` | **PASS** |
| Parallel paths section | **PASS** |
| UI severity + screenshots | **PASS** |
| Simplification Nivel 1/2/3 fără încălcarea ownership | **PASS** |
| Scoruri + next prompt | **PASS** |
| Secțiune Product Template → Modules (8A) | **PASS** |

---

*End of audit. No functional code was changed. Section 8A added 2026-07-23 (Product Template → Modules mental-model completion).*
