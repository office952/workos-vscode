# WORKOS — PRODUCT SYSTEM FULL-PAGE UI TRUTH AUDIT

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Mode | **READ-ONLY** — no code/CSS/Figma/schema/data/test edits; no commit |
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `033f28fee016752622debba4f5a1817303d9a1ef` (`033f28f`) — **reconfirmed** |
| Fixture | `TPL-VOLUMETRIC-LETTERS_v2` |
| Aluminiu | **inactive** — not activated (accepted prior) |
| Screenshots | `docs/qa/product-system-authoring-runtime-codesign-e2e/ui-truth-audit/` (**22 PNG**) |
| Verdict | **STOP before further PS UI implementation** — clarity FAIL for 10s admin test; stack + publication honesty gaps |

---

## 1. Kickoff confirmation

| Item | Result |
|------|--------|
| Repo root | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `033f28fee016752622debba4f5a1817303d9a1ef` matches reported `033f28f` |
| Working tree | Dirty (~hundreds preserved; unrelated + WIP) — **not cleaned** |
| FE runtime | `:3000` **UP** (default Vite; proxy `BACKEND_PORT` default **8001**) |
| BE runtime | `:8000` **UP** (has publication + e2e-readiness); `:8001` **UP** (catalog/aggregate OK; **missing** publication + e2e-readiness → **404**); `:8011` UP (same gap) |
| API base (operator FE:3000) | Same-origin `/api` → **8001** |
| API base (aligned capture FE:3020) | Same-origin `/api` → **8000** (temporary Vite, read-only screenshots) |
| Primary routes | `/product-system/products`, `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2`, `/product-system/blueprint-dossier?template=…` |
| Planned shell routes | `/product-system/{components,resources,operations,dependencies,validation,advanced}` → placeholder pages |
| Families route | **No** dedicated `/product-system/families` — family shown inside catalog/detail |
| Prior accepted state | VL Real Product Config PASS; publication/components BLOCKED; CPP→EP NOT_TESTED; Aluminiu inactive — **not reopened for activation** |

---

## 2. Absolute boundaries (honored)

- No code/CSS/component edits
- No Figma edits
- No schema/data/status/lifecycle changes
- No Aluminiu activation
- No Product System data modifications
- No test modifications
- No commit/push/PR
- No new implementation build
- Allowed: inspect, runtime screenshots, Figma read-only MCP, one audit report + worklog pointer

---

## 3. Central question — 10-second admin test

**Can a PS admin understand in ~10 seconds: product open; state; config complete?; publication possible?; why blocked?; next action?; business vs technical?**

| Question | Verdict (runtime) |
|----------|-------------------|
| Product open? | **YES** — human name “Litere volumetrice” + code visible |
| State? | **PARTIAL** — `BUILD ACTIV` clear; publication confused (`HTTP 404` on default FE, or `LEGACY_UNSPECIFIED` on aligned BE) |
| Config complete? | **UNCLEAR in 10s** — dual chips ≠ config completeness; composition buried in tabs |
| Publication possible? | **NO (truth)** Aluminiu inactive — but **UI lies on aligned BE**: green **Publică** enabled with empty `publish_blockers` while readiness `verdict=BLOCKED` |
| Why blocked? | **PARTIAL** — Readiness findings show Aluminiu when API works; default FE:3000 → readiness/publication **404** so why-blocked fails |
| Next action? | **NO** — no single “next step” hero; sticky Save→Validate→Check→Publish only on Dossier Studio; catalog badge soup |
| Business vs technical? | **WEAK** — human names improved; English BUILD/TEMPLATE/LEGACY codes still primary visual weight |

**Overall 10s clarity: FAIL** (usable by trained owner with context; not honest for a cold PS admin).

---

## 4. Runtime topology (critical evidence)

```text
FE :3000  ──proxy──► BE :8001  → template-availability OK
                                → /templates/{code}/publication     404
                                → /e2e-readiness/{code}/static      404

FE :3020  ──proxy──► BE :8000  → publication 200
                                → e2e-readiness/static 200
                                → dual-axis fields often null in response
                                → publish_allowed=true despite readiness BLOCKED
```

**Stop/blocker for screenshots:** none for page chrome — all primary routes rendered. **ENVIRONMENT_FAILURE** on default stack for publication/readiness APIs (404). Aligned stack used only to prove panel content when endpoints exist.

---

## 5. Routes inventory (real)

| Route | Operational? | Notes |
|-------|--------------|-------|
| `/product-system` | redirect → products | |
| `/product-system/products` | **YES** | Canonical catalog |
| `/product-system/products/:templateCode` | **YES** | Detail + authoring tabs |
| `/product-system/blueprint-dossier` | **YES** | Outside shell layout; sticky footer |
| `/product-system/components` (+ peers) | **Placeholder** | `Planificat` + message |
| `/product-system/output-blocks-preview` | Separate preview | Not in shell nav |
| Families / Contracts / Preview / Readiness / Publication as **top-level shell** | **NO** | Live as **detail tabs** on product template |

---

## 6. Fixture / template truth (accepted, not reopened)

| Axis | Accepted | Live recheck |
|------|----------|--------------|
| VL Real Product Config | PASS | Composition/contracts UI present |
| Components (Aluminiu) | BLOCKED | Readiness finding: required inactive `TPL-VOLUM-ALUMINIU_v1` |
| Publication | BLOCKED | Truth intent yes; **publication API not fail-closed** on BE:8000 |
| CPP → EP | NOT_TESTED | System Link Check rows show NOT_TESTED |
| Aluminiu activation | No GO | Still inactive |

Prior evidence file `runtime/vl_real_product_config_system_link_check.json`: Catalog/Intake/PD/Agg/Qty stronger; Components BLOCKED; CPP/EIC/… NOT_TESTED; publication BLOCKED Aluminiu.

Live BE:8000 static readiness also reported a **false catalog BLOCKED** (`TPL-VOLUMETRIC-LETTERS_V2` uppercase lookup) alongside Aluminiu — see §14 / §24.

---

## 7. Part A — Top-of-page elements (every layer)

Observed top-of-page stack (product detail, FE:3000):

1. **App chrome** — WorkOS sidebar + top search + “Stare sistem: necesită verificare”
2. **PS shell H1** — “Product System” + subtitle pipeline + **Pricing Registry** link (action)
3. **PS shell nav** — Products + 6× **Planificat** NavLinks
4. **Catalog toolbar** — search, Live DB, filter chips (Toate operaționale, Blocat, …)
5. **List card badges** — Rădăcină / De sine stătător / Blocat (pregătire) / N blocaje
6. **Detail header** — Șablon produs · human name · code · **TemplateDualStatusChips** · Status catalog `<details>`
7. **Primary tabs** — Prezentare → … → Publicare → Runtime Preview
8. **Diagnostic tabs** — Componente / Relații / Materiale / Diagnostic (secondary weight)

### Planificat — code + runtime (not enum excuse)

| Question | Answer |
|----------|--------|
| Button vs status? | **Neither lifecycle status nor CTA** — small uppercase **badge on a NavLink** (`PRODUCT_SYSTEM_PLANNED_BADGE_RO = "Planificat"`) |
| Entity? | **Shell section** (`plannedSection: true` on Components/Resources/Operations/Dependencies/Validation/Advanced) — **not** a product template state |
| Who? | Product System **admin shell** honesty for unfinished areas |
| Action on click? | Navigates to `ProductSystemPlannedSectionPage` — dashed empty state + “Înapoi la Products” |
| Lifecycle / roadmap / impl / prod? | **Roadmap / implementation placeholder** — explicitly “Secțiune neoperațională” |
| Belong in PS? | **Yes as shell meta** — prevents fake-complete admin sections |
| Replacement? | Optional label **“În curând”** / **“Neoperațional”**; or collapse planned items under “Mai mult” |

**Dedicated decision → §20.**

---

## 8. Part B — Status semantics inventory

Statuses today appear as **equal visual badges**. Required separation:

| Layer | Examples in UI | Should look like |
|-------|----------------|------------------|
| **Config / composition** | module links, used-by, materials lists | Progress / checklist, not badge soup |
| **Lifecycle (catalog)** | Build activ/inactiv, Live DB | Single durable chip |
| **Publication** | LEGACY_UNSPECIFIED, DRAFT…PUBLISHED, publish_allowed | Distinct **gate** strip; blocked banner primary |
| **System integration** | System Link Check hops | Table / pipeline, not catalog chips |
| **Runtime-job** | workspace dry-run | Explicit “job check” mode |

**Current failures:** list cards mix commercial/role/blocker chips at same weight; dual chips fight filter chips; Planificat badges sit next to Products like peer states; dossier “Aprobat” can be misread as product publishable.

---

## 9. Part C — Full-page visual / darkness / WorkOS match Q1–10

### Darkness root cause (one line)

**WorkOS global shell `bg-[#0A0F1C]` plus PS nested panels `#0B1220` / `#0D1321` / `#111827` with near-zero luminance separation — theme-level dark admin, amplified by dual-column density and rainbow badges; not a Figma-only artifact.**

### Nesting / density

- App shell → PS shell → catalog chrome → list+detail → tab chrome → panel cards → nested details
- Figma PS frames are **annotation shells** (dark canvas + text), not high-fidelity surfaces — they **reinforce** darkness but are not the runtime root

### WorkOS visual match questions

| # | Question | Answer |
|---|----------|--------|
| 1 | Same global shell as Inventory/Intake? | **YES** — identical sidebar/topbar |
| 2 | Same page header weight? | **PARTIAL** — PS denser (pipeline subtitle + Pricing Registry + Planificat nav) |
| 3 | Surface tokens match? | **YES** — shared dark navy family |
| 4 | Badge language match? | **NO** — Intake uses clearer workflow KPIs; PS mixes EN codes + RO chips |
| 5 | Primary CTA clarity? | **NO** — Intake has `+ Cerere Nouă`; PS detail has no single next CTA |
| 6 | Empty/placeholder honesty? | **YES** for Planificat pages; **NO** for enabled Publică when blocked |
| 7 | List→detail pattern? | **YES** — similar master-detail |
| 8 | Warning banners? | Shared system banner; Inventory uses stronger page banners |
| 9 | Visual comfort? | **LOW** on PS detail (more nesting than Intake list) |
| 10 | Pixel/Figma FINAL? | **NO** — Figma NEEDS_POLISH / DESIGN_ONLY |

---

## 10. Part D — WorkOS visual alignment table

References captured live: Inventory (`13_…`), Governance (`14_…`), Work Intake (`15_…`).

| Property | PS now | WorkOS ref (Intake / Inventory) | Direction |
|----------|--------|----------------------------------|-----------|
| Page job in first viewport | Multi-job: catalog + detail + status soup | One job: list requests / stock table | **Simplify PS first viewport to one job** |
| Primary CTA | Diffuse (tabs / sticky only in Dossier) | Clear (`+ Cerere Nouă` / stock actions) | **Add next-action strip on template** |
| Status model | Many equal badges | KPI cards + few row statuses | **Layer statuses (lifecycle ≠ publication ≠ blockers)** |
| English vs RO | Mixed (BUILD, LEGACY, Runtime Preview) | Mostly RO operator labels | **RO primary labels; codes secondary** |
| Surface nesting | 4–5 nested dark boxes | 2–3 | **Flatten panels** |
| Honesty empty states | Planificat good | Intake empty detail good | Keep; fix publication honesty |
| Darkness | Same theme family | Same | Comfort via contrast + spacing, not light theme rewrite |
| Sticky actions | Dossier only | Intake footers elsewhere | Align Save→Validate→Check→Publish on template OR link-only to Studio |

---

## 11. Part E — Information hierarchy test

**Recommended hierarchy (evidence-based):**

| Priority | Content | Placement |
|----------|---------|-----------|
| P0 first viewport | Product human name + one lifecycle chip + one publication gate + **next action** + top blocker | Detail header only |
| P1 | Composition summary (required/optional counts) | Overview or Compoziție |
| P2 | Readiness dual axes + System Link Check | Readiness tab (expand) |
| P3 | Contracts / Runtime Preview diagnostics | Tabs / collapse |
| Collapse | Modularity honesty, Status catalog, technical evidence | `<details>` |
| Separate route | Blueprint Dossier Studio (already) | Keep deep-link |
| Remove / demote | Equal-weight Planificat row; diagnostic tabs as peer to Publicare | Shell / secondary |

**Now:** first viewport fails hierarchy — filter chips + list badges + dual chips + tab rows compete.

---

## 12. Part F — Action audit

| Action | Where | Match Save→Validate→E2E→Publish? | Notes |
|--------|-------|----------------------------------|-------|
| Pricing Registry | Shell header | No | External jump OK |
| Planificat NavLinks | Shell | No | Fake-looking peers; honest destination |
| Catalog filters | Catalog | No | Filter ≠ status |
| Primary authoring tabs | Detail | Partial flow | Order OK conceptually |
| Verificare statică | Readiness | = Check | Good when API exists |
| Runtime dry-run | Readiness | Check mode | Needs workspace_id |
| Intră în DRAFT / Marchează E2E_CHECKED / **Publică** | Publication | Yes | **Publică enabled while readiness BLOCKED** on BE:8000 |
| Sticky Salvează / Validează / Verifică / Publică | Dossier Studio | **Yes** | Present; Publică not hard-disabled by readiness in chrome |
| Composition “Salvează contract” | Composition | Save only | OK |
| Disabled without explanation | Various | — | Publică **enabled without blocker banner** when API returns empty blockers |

**Fake clickables:** Planificat tabs look like operational peers until opened; filter chips look like status truth.

---

## 13. Part G — Terminology (user-facing names)

| Internal | Current UI | Recommended user-facing |
|----------|------------|-------------------------|
| Product Template | Șablon produs | **Șablon produs** (keep) |
| Component Contract | Contracte / child PT | **Contract componentă** |
| PD | ProductDefinition (codes) | **Definiție produs** |
| Aggregate | Aggregate | **Agregat produs** |
| Runtime Preview | Runtime Preview | **Previzualizare runtime** |
| Dossier | Dossier / Blueprint Dossier | **Dosar tehnic** (+ Blueprint subtitle) |
| Bridge | (dossier internals) | **Punte documentară** (not BOM) |
| Usage Mode | Utilizare / rădăcină ofertabilă | **Mod de utilizare** |
| Provenance | evidence / mono codes | **Proveniență** under details |
| System Link Check | System Link Check | **Verificare legături sistem** |
| E2E Readiness | Readiness / Verifică traseul | **Pregătire E2E** |
| Planificat | Planificat | **Neoperațional** / **În curând** (shell only) |
| Active | Build activ / Catalog activ | **Activ în catalog** |
| Published | Publicare / PUBLISHED | **Publicat** |
| Offerable | rădăcină ofertabilă | **Ofertabil** (only if publication gate true) |

---

## 14. Part H — System Link Check UI

**Must show:** path stop / blocker / owner / next / untested.

| Requirement | Runtime |
|-------------|---------|
| Path table Catalog→EP | **Yes** when static check succeeds (aligned BE) |
| Stop/blocker | Findings list + blocking tags; Aluminiu called out |
| Owner / next | **Weak** — no owner column; no single next step |
| Untested | NOT_TESTED rows present |
| Known stronger hops | Prior evidence: Catalog/Intake/PD/Agg/Qty PASS; live aligned BE polluted by false **catalog BLOCKED** (case `…_V2`) |
| Components BLOCKED | **Yes** (Aluminiu inactive) |
| CPP→EP NOT_TESTED | **Yes** |
| Publication BLOCKED Aluminiu | Readiness yes; **Publication panel not synced** |

Default FE:3000: System Link Check **does not load** (HTTP 404) — admin sees only “Verificare statică” without axes.

---

## 15. Part I — Figma read-only

| Item | Value |
|------|-------|
| File | `0CDPIuqoaZ1OQgNnvNyl1F` |
| Page | `PS — Authoring Studio` (`91:2`) — metadata confirmed |
| Method | `get_metadata` + `get_screenshot` — **no edits** |

| Frame | ID | Class |
|-------|-----|-------|
| PS Template Authoring Shell | `91:3` | **NEEDS_POLISH** — annotation wire, not runtime parity |
| Component Contract + Used-by | `91:12` | NEEDS_POLISH |
| Blueprint Dossier Studio split | `91:21` | NEEDS_POLISH |
| StickyPublishFooter nested | `91:32` | NEEDS_POLISH |
| Publication states | `91:36` | NEEDS_POLISH |
| Readiness PASS / BLOCKED | `91:60` | NEEDS_POLISH — honesty intent OK |
| Pack shells `91:76`–`91:100` | DESIGN_ONLY | placeholders |
| Intake Confirmare / PinFooter | `66:2` / `67:18` | FINAL refs (untouched) |

**Figma darkness source:** dark annotation canvas + text frames — **not** a complete visual system; runtime darkness is App shell tokens (§9).

---

## 16. Part J — Screenshot inventory (22)

Directory: `docs/qa/product-system-authoring-runtime-codesign-e2e/ui-truth-audit/`

| # | File | Subject |
|---|------|---------|
| 1 | `01_ps_landing_products.png` | Landing products |
| 2 | `02_ps_planificat_components.png` | Planificat section page |
| 3 | `03_ps_shell_nav_planificat_badges.png` | Shell nav badges |
| 4 | `04_vl_template_overview_dual_chips.png` | VL overview (FE:3000; Publicare HTTP 404) |
| 5 | `05_vl_composition.png` | Composition |
| 6 | `06_vl_contracts.png` | Contracts |
| 7 | `07_vl_dossier_tab.png` | Dossier tab |
| 8 | `08_blueprint_dossier_studio.png` | Dossier Studio |
| 9 | `09_sticky_save_validate_check_publish.png` | Sticky footer |
| 10 | `10_vl_runtime_preview.png` | Runtime Preview |
| 11 | `11_vl_readiness_system_link.png` | Readiness on default stack |
| 12 | `12_vl_publication.png` | Publication on default stack |
| 13 | `13_workos_ref_inventory.png` | WorkOS Inventory ref |
| 14 | `14_workos_ref_governance.png` | WorkOS Governance ref |
| 15 | `15_workos_ref_intake.png` | WorkOS Intake ref |
| 16 | `04b_vl_overview_aligned_be8000.png` | Overview aligned BE:8000 |
| 17 | `11b_vl_readiness_aligned_be8000.png` | Readiness + findings aligned |
| 18 | `12b_vl_publication_aligned_be8000.png` | Publication (Publică enabled) |
| 19 | `09b_sticky_footer_aligned_be8000.png` | Sticky aligned |
| 20 | `figma_91_3_ps_authoring_shell.png` | Figma shell |
| 21 | `figma_91_21_blueprint_dossier.png` | Figma dossier |
| 22 | `figma_91_60_readiness.png` | Figma readiness |

Evidence JSON: `ui-truth-audit/capture_evidence.json` (FE:3000 console: multiple **404**).

---

## 17. Part K — Audience / ownership per block

| Block | Audience | Owner |
|-------|----------|-------|
| Shell Planificat nav | PS admin | Product System UX + platform |
| Catalog list / filters | PS admin | Catalog model owner |
| Dual status chips | PS admin | Publication + readiness contract |
| Composition / contracts | PS admin + template owner | Authoring |
| Dossier Studio | Docs/config owner | Blueprint dossier |
| Readiness / System Link | Owner / QA gate | E2E readiness service |
| Publication actions | Owner only | Publication gate (must sync readiness) |
| Runtime Preview | Admin diagnostic | Runtime preview adapter |
| Artwork analysis panel | Boundary note | External analysis (out of WorkOS parse) |

---

## 18. Part L — Recommended target page (textual wireframe)

Evidence-based — **not** blind Figma copy:

```text
┌─────────────────────────────────────────────────────────────┐
│ Product System / Products / Litere volumetrice              │
│ [Activ în catalog]     [Publicare: BLOCATĂ]                 │
│ Motiv: Aluminiu (copil obligatoriu) inactiv                 │
│ Următorul pas: deschide Pregătire E2E → sau așteaptă GO     │
│                                              [Dosar tehnic] │
├─────────────────────────────────────────────────────────────┤
│ Flux: Prezentare | Compoziție | Contracte | Pregătire E2E | │
│       Publicare | Previzualizare     ··· Diagnostic ▾       │
├──────────────┬──────────────────────────────────────────────┤
│ Catalog      │  Prezentare: business summary only           │
│ (slim)       │  — utilizare, work intake, 5+2 componente    │
│              │  Technical codes in <details>                │
└──────────────┴──────────────────────────────────────────────┘
Footer (template OR studio): Salvează → Validează → Verifică → Publică
  Publică disabled + reason when readiness ≠ publishable
```

Shell: keep Products primary; **demote** Planificat items to “În curând” overflow — not equal tabs.

---

## 19. Part M — Change plan (DO NOT IMPLEMENT)

### P0 — honesty / clarity blockers

1. **Fail-closed publication UI+API** — never enable Publică when readiness BLOCKED / Aluminiu inactive; show blockers human-primary.
2. **Fix FE↔BE stack for authoring APIs** — FE proxy must hit BE that serves `/publication` + `/e2e-readiness` (or document single canonical port).
3. **First-viewport next-action + why-blocked** — one strip; demote badge soup.

### P1 — status / hierarchy

4. Separate visual languages for lifecycle vs publication vs System Link vs Planificat shell meta.
5. System Link Check: stop hop, owner, next action columns; fix false catalog case mismatch.
6. Dual-axis fields populated consistently (`build_closure_status` / `template_publication_status`).

### P2 — WorkOS alignment / comfort

7. Flatten nested dark panels; increase surface contrast without abandoning WorkOS dark theme.
8. RO labels for Runtime Preview / Readiness / System Link Check.
9. Sticky action parity: template page summary OR stronger Dossier CTA (already partially present).

### P3 — Figma / polish

10. Redraw PS Authoring Studio frames against runtime (not annotation-only); promote FINAL only after owner.
11. Optional Planificat rename + overflow nav.
12. Catalog filter/chip visual quieting.

---

## 20. PLANIFICAT — KEEP / RENAME / MOVE / REMOVE

| Field | Value |
|-------|--------|
| **Technical meaning** | `plannedSection?: true` on `PRODUCT_SYSTEM_SHELL_NAV` items; badge text `PRODUCT_SYSTEM_PLANNED_BADGE_RO`; route renders `ProductSystemPlannedSectionPage` with `data-operational="false"` |
| **Runtime meaning** | Clickable nav item → honest non-operational placeholder; **not** product lifecycle, not publication, not job status |
| **Decision** | **KEEP** (shell honesty) |
| **Also** | **RENAME** user-facing to **“Neoperațional”** or **“În curând”** (optional P3) |
| **MOVE** | Visually to overflow / right cluster (Advanced already `ml-auto`) — reduce peer weight with Products |
| **REMOVE** | **Do not remove** without replacing honesty — otherwise admins will invent fake Components/Resources admin |
| **Must not** | Appear as equal status chip beside BUILD / Publicare on product header |

---

## 21. 10-second clarity answers (packed)

See §3. **FAIL** for cold admin; **PARTIAL** for trained owner when aligned to BE:8000.

---

## 22. Business vs technical separation

| Good | Bad |
|------|-----|
| Human name primary on detail header | LEGACY_UNSPECIFIED / BUILD NOT_TESTED as hero |
| Aluminiu humanized in findings | List cards with 4+ chips |
| activ ≠ publicat chip | Publică green while blocked |
| Planificat explanation copy | Planificat looking like product state |

---

## 23. Publication honesty gap (P0)

Live `GET …/publication` on BE:8000 for VL:

- `publish_allowed: true`
- `publish_blockers: []`
- `effective_status: LEGACY_UNSPECIFIED`
- UI shows **Publică** enabled

Live readiness static: `verdict: BLOCKED` with Aluminiu inactive finding.

**Contradiction:** copy says “Publicarea e blocată de E2E Readiness” while actions contradict. This fails the central question harder than darkness.

---

## 24. Runtime / data noise affecting UI truth

1. FE:3000 → BE:8001 **404** on publication/readiness → chips show **PUBLICARE — HTTP 404**
2. Readiness catalog check may uppercase template code → false “not found in catalog”
3. Dual-axis statuses often **null** → UI falls back to BUILD NOT_TESTED / TEMPLATE PUBLICATION NOT_READY even after static run
4. Prior evidence JSON remains the better **intended** System Link truth than a noisy live BE instance

---

## 25. Comparison to accepted prior state

| Prior | This audit |
|-------|------------|
| VL config PASS | UI shows composition/contracts — accepted |
| Publication BLOCKED Aluminiu | Intent preserved; **panel/API not fail-closed** |
| Components BLOCKED | Visible in readiness findings (aligned) |
| CPP→EP NOT_TESTED | Visible |
| No activation GO | Honored |

**Do not treat prior UI PASS_WITH_WARNINGS as still true for 10s clarity** — stack + publication honesty regress/expose gaps.

---

## 26. Direction scores (0–100)

| Axis | Score | Note |
|------|------:|------|
| Information clarity | **38** | Product identity OK; completeness/next action fail |
| WorkOS visual alignment | **55** | Same shell/tokens; denser / noisier than Intake |
| Action clarity | **32** | Sticky exists in Studio; Publică honesty broken; Planificat peer noise |
| Status coherence | **28** | Layers conflated; dual chips vs filters vs Planificat |
| Visual comfort | **40** | Theme-consistent but nested dark-on-dark fatigue |

**Composite (unweighted mean): ~39/100 — STOP.**

---

## 27. Max 3 owner decisions (if unavoidable)

1. **Canonical authoring stack port** — declare BE that owns publication + readiness; FE proxy must match (ops decision, not Aluminiu).
2. **Publication fail-closed policy** — confirm Publică must hard-gate on readiness BLOCKED even if `publication_status` is legacy NULL.
3. **Planificat label** — KEEP vs RENAME to “Neoperațional” (cosmetic; KEEP semantics).

No Aluminiu activation decision requested here.

---

## 28. Roadmap awareness confirmations

| Confirmation | Status |
|--------------|--------|
| Planificat sections are roadmap placeholders, not product states | **Confirmed** (code + runtime) |
| Products is the only operational shell section today | **Confirmed** |
| Save→Validate→Check→Publish lives on Dossier sticky | **Confirmed** |
| Figma PS frames are PROPOSED / NEEDS_POLISH, not FINAL | **Confirmed** |
| Aluminiu inactive blocks honest publication | **Confirmed** (readiness); UI/API sync **broken** |
| Further PS UI implementation should wait for this STOP | **Recommended** |

---

## 29. Stop / do not implement

**Owner STOP before further PS implementation** until P0 items in §19 are accepted into a dedicated build. This audit does **not** start that build.

---

## 30. Evidence index

- Screenshots: `ui-truth-audit/*.png` (22)
- Capture evidence: `ui-truth-audit/capture_evidence.json`
- Prior System Link: `runtime/vl_real_product_config_system_link_check.json`
- Code: `productSystemShellConfig.ts`, `ProductSystemLayout.tsx`, `ProductSystemPlannedSectionPage.tsx`, `TemplateDualStatusChips.tsx`, `ProductE2EReadinessPanel.tsx`, `ProductTemplatePublicationPanel.tsx`, `BlueprintDossierStudio.tsx` sticky footer, `App.tsx` routes
- Figma: file `0CDPIuqoaZ1OQgNnvNyl1F` page `91:2`

---

## 31. Files written (no commit)

| File | Role |
|------|------|
| `docs/qa/product-system-authoring-runtime-codesign-e2e/PRODUCT_SYSTEM_FULL_PAGE_UI_TRUTH_AUDIT.md` | This report |
| `docs/qa/product-system-authoring-runtime-codesign-e2e/ui-truth-audit/*` | Screenshots + capture script/evidence |
| `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` | Pointer section appended |

---

## 32. Commands run (read-only)

- `git rev-parse` / `git status` / `git log -1`
- HTTP probes to `:8000` / `:8001` / `:3000` / `:3020` product-system endpoints
- Playwright capture scripts against FE:3000 and FE:3020 (`BACKEND_PORT=8000`)
- Figma MCP `get_metadata` / `get_screenshot` (read-only)
- Temporary Vite `:3020` for aligned screenshots only

---

## 33. PAREREA MEA SINCERA

Pagina PS arată ca un **control center de inginerie**, nu ca o pagină de admin de produs. Planificat e onest în copy, dar **fură atenția** ca și cum ar fi status de produs. Întunericul nu e “bug de culoare PS” — e tema WorkOS + panouri stivuite; se rezolvă cu ierarhie și contrast, nu cu redesign violet. Cel mai grav: pe stack-ul default publicarea/readiness dau 404, iar pe BE-ul “bun” **Publică e verde în timp ce E2E e BLOCKED** — asta e minciună operațională, nu polish. STOP înainte de încă un build de UI e corect.

---

## 34. Final verdict summary

| Item | Result |
|------|--------|
| 10s admin clarity | **FAIL** |
| Planificat | **KEEP** (+ optional RENAME/MOVE visual) |
| Darkness | Theme shell + nested low-delta surfaces |
| Publication honesty | **BROKEN** vs readiness |
| Default FE stack | **ENVIRONMENT_FAILURE** for pub/readiness APIs |
| Screenshot count | **22** |
| HEAD | `033f28f` |
| Next | Owner decisions §27 → then P0-only build (not this audit) |

**STOP.**
