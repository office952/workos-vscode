# S5 research note — Product System / Governance chrome truth

| Field | Value |
|-------|--------|
| Task | `S5_PRODUCT_SYSTEM_AND_GOVERNANCE_CHROME_TRUTH_V1` |
| Phase | ROOT-CAUSE RESEARCH ONLY |
| Date | 2026-08-14 |
| HEAD | `17e4b5359347f00265459d932ef5d8e571dbe693` |
| Implementation | NO |
| Unfreeze | NO |
| Commit | NO |
| Push | NO |

Runtime inspected as **admin** on live stack (`:3000` + `:8000`). Manager role switch is not in the user menu; manager/sales visibility is from RBAC.

## Research A — Product System entry

| Field | Value |
|-------|--------|
| PRODUCT_SYSTEM_ENTRY_ROUTE | `/product-system/products` |
| PRODUCT_SYSTEM_ENTRY_COMPONENT | `ProductSystem` inside `ProductSystemLayout` (`App.tsx`) |
| PRODUCT_SYSTEM_NAV_SOURCE | `shellNavigation.ts` Lucrări → **Produse** |
| PRODUCT_SYSTEM_VISIBLE_ROLES | `sales`, `manager`, `admin` (`view:products`). Operator/viewer: no. |
| PRODUCT_SYSTEM_CURRENT_TITLE | `Produse și șabloane` |
| PRODUCT_SYSTEM_CURRENT_SUBTITLE | `Structură produs și șabloane — definire înainte de ofertă. Nu stabilește preț client sau Product Truth runtime.` |
| PRODUCT_SYSTEM_CURRENT_STATUS_BADGES | `Live DB`; spine chips `Product Template / Structură produs / Product Compiler / Pregătire` |
| PRODUCT_SYSTEM_CURRENT_PRIMARY_CTAS | `Deschide oferte` → `/quotes`; `Înapoi la cereri` → `/intake` |

Default workspace: `ProductSystemV2Workspace`. Legacy catalog: `?ps_legacy=1` (no in-app link from V2).

**Perception: AMBIGUOUS**

The subtitle is honest (design / authoring). The first-fold chrome then pulls toward a live catalog / commercial next step:

- rail heading **Produse active**
- next-step **Continuă spre ofertă**
- numbered spine that looks like a workflow
- ACM listed as a peer of Letters

Not MISLEADING as a commercial catalog (copy says offer is created elsewhere). Not CLEAR as design-only.

## Research B — product spines / dual truth

| Product | Template | Runtime authority | Authoring direction | UI message now |
|---------|----------|-------------------|---------------------|----------------|
| Litere volumetrice | `TPL-VOLUMETRIC-LETTERS_v2` | **ACTIVE** — owner-valid root, Work Intake yes | Legacy shared modules (`TPL-VOLUMETRIC-FACE_v1` etc.) | In **Produse active**; structure Față / Volum / Spate / LED |
| Logo | `TPL-VOLUMETRIC-LOGO_v1` | **INACTIVE / blocked root** | Candidate / linked-child | **Not in rail.** Deep-link: `Template necunoscut în listă` |
| Panouri ACM | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` (live); `TPL-ACM-CASSETTED-PANEL` archived | Policy: **root-offerable** with Letters (`activeTemplateScope.ts`). `/modules`: **ACM PARTIAL**. Modularity copy: montaj parțial / casetat arhivat | Boxed mounting, not independent cassette | Rail: **Alucobond casetat** under **Produse active**, no PARTIAL chip |

Component-first (`TPL-LETTERS-COMPOSER_v1` + `TPL-COMP-LETTER-*`): **INACTIVE / CANDIDATE / READONLY / NOT OFFERABLE**. Reachable via legacy catalog / deprecated editor, not V2 rail.

**UI relation: LEGACY_PRIMARY_COMPONENT_FIRST_SECONDARY**

Do **not** choose a new runtime authority in S5. Letters is the live spine. Component-first is direction, not runtime. ACM boxed is policy-offerable and PARTIAL in the system map — chrome should show that split, not deactivate the template.

## Research C — unwired / inactive shells

Planned routes (`/product-system/components` … `/advanced`) are **hidden from nav** and honest on URL: `ÎN DEZVOLTARE` / `Secțiune neoperațională`. GS-11 “hide planned shells” is largely already done.

Remaining GS-11 work is on the **live V2 workspace**, not those placeholders.

| Candidate | Classification | Perception |
|-----------|----------------|------------|
| Planned section pages | INACTIVE | HONEST |
| Spine band 1–4 | PLACEHOLDER | AMBIGUOUS |
| V2 rail “Produse active” + ACM peer | ACTIVE_AND_WIRED (policy) | AMBIGUOUS vs `/modules` PARTIAL |
| ACM human name = archived cassette name | ACTIVE_AND_WIRED | AMBIGUOUS |
| Logo deep-link empty | INACTIVE | AMBIGUOUS (says unknown, not blocked) |
| Prețuri conexiune 20 EUR/mp card | READ_ONLY_VALID (owner-locked șablon) | MISLEADING as price authority |
| Composer mock IA card | DEMO | HONEST |
| Next-step “Continuă spre ofertă” | ACTIVE_AND_WIRED (nav only) | AMBIGUOUS vs S1 “PS is not a FLUX step” |
| Publication / E2E / Laborator vechi | ACTIVE_AND_WIRED, admin drawer | HONEST when collapsed |
| Dead `ProductSystemCatalogShell` | NOT_WIRED | no owner impact |
| Candidate catalog variant | NOT_WIRED | — |

## Research D — authoring vs runtime

| Layer | Source | Owner-visible without docs? |
|-------|--------|-----------------------------|
| Authoring | template JSON + composition links | PARTIAL — V2 is readonly structure |
| Runtime Product Truth | ProductDefinition preview API | PARTIAL — admin tab only |
| Publication | publication API; chips Activ în catalog ≠ Publicare | PARTIAL — admin / legacy detail |
| Pricing readiness | availability.readiness.pricing | CONFUSED with 20 EUR card |
| Execution readiness | availability.readiness.execution | PARTIAL — collapsed “Alte sisteme” |

**Boundary: PARTIAL / CONFUSED** on first fold. Honesty exists in subtitle + collapsed technical details, not in the rail/cards.

## Research E — Dossier

| Field | Value |
|-------|--------|
| DOSSIER_ROUTES | `/product-system/blueprint-dossier` (active); `/product-system/dossier-completion` (redirect) |
| DOSSIER_COMPONENTS | `BlueprintDossierStudio`; `DossierCompletionDashboard` unrouted |
| DOSSIER_NAV_LINKS | DEV tooling only (`status: audit`) |
| DOSSIER_HANDOFF_LINKS | all live links → canonical studio |

**ONE_CANONICAL_DOSSIER.** OWNER_DECISION_REQUIRED for dual dossiers = **NO**.

## Research F — Guards / Audit

No `PRODUCT_SYSTEM_GUARDS_ROUTE`. Guards live as a **tab** on the candidate panel and as Diagnostic/Garduri on legacy template detail.

Primary V2 chrome does **not** dump `not_ready_for_delete` / replacement tables. Those stay audit-only.

`PRIMARY_CHROME_AUDIT_LEAK_COUNT = 0` for machine-audit tables. Secondary honesty chips / `MODULE_MODEL_DEFERRED` on planned page are acceptable.

## Research G — `/modules`

| Field | Value |
|-------|--------|
| MODULES_ROUTE | `/modules` |
| MODULES_COMPONENT | `ModuleChain` |
| MODULES_STATUS_SOURCE | `currentTruthControlCenter.ts` + health API 30s |
| MODULES_FREEZE_INDICATOR | commercial/snapshot freeze only |
| MODULES_LAST_SYNC_SIGNAL | `Ultima verificare` from health `generated_at` |

Repo freeze `CURRENT_WORKOS_FROZEN_AS_REFERENCE = ON`: **MISSING**.

Product System card: **Catalog produse / PARTIAL**. PD/PA: Product Compiler labels, PARTIAL. Intake V6: CONFIRMAT. Execution: PARTIAL. Active Scope: Logo BLOCKED, ACM PARTIAL — matches research B, **not** the V2 rail.

Visible only to **admin** (`view:modules`).

## Research H — `/governance`

| Field | Value |
|-------|--------|
| GOVERNANCE_ROUTE | `/governance` |
| GOVERNANCE_COMPONENT | `Governance` |
| GOVERNANCE_FREEZE_INDICATOR | none for repo freeze; `g.owner_frozen` = commercial snapshot |
| GOVERNANCE_OWNER_GATE_PRESENTATION | Owner gates tab + ownership matrix |

Repo freeze: **MISSING**. S1–S4 bounded-exception model: **MISSING**.

GS-13 still present: tab **Catalog produse (referință)** — 12 static families / 50 rows, badge `REFERINȚĂ`, note “Catalogul activ este /product-system.” Honesty exists; the grid still looks like a live nomenclator.

Admin-only (`view:governance`).

## Research I — registration

Wave 4: `TRUE_UNREGISTERED_SYSTEM = 0`, `TRUE_UNREGISTERED_CAPABILITY = 0`. Reconfirmed: no new Level-1 Product System capability is active-looking and unregistered.

Composer mock + output-blocks-preview = audit/demo, not unregistered systems.

## Research J — DEV MODE

Canonical DEV MODE (new/versioned copy, frozen operational version untouched): **ABSENT**.

Present instead: `DEV MOCK` chip when mock load; authoring-stack banner; DEV tooling nav; `publication_version` field (no DEV-version banner).

No fake “DEV MODE” button. Do **not** implement DEV MODE in S5.

## Research K — nav / shortcuts

| Channel | Destinations |
|---------|--------------|
| PRIMARY_NAV | Produse → `/product-system/products` |
| DASHBOARD_SHORTCUTS | none to Product System |
| PAGE_LOCAL_LINKS | structure pages, next-step quotes/intake, admin editor |
| DOSSIER_LINKS | one studio |
| GUARD_LINKS | `/modules`, `/governance` from some footers |
| AUDIT_LINKS | Blueprint Dossier (DEV) |
| INTAKE_LINKS | Intake → `/product-system`; PS → `/intake-v6/operator` |

**MULTIPLE_VALID_PROJECTIONS** (V2 / legacy query / structure / dossier). Not duplicate product-truth destinations.

## Role split (material)

| Role | Produse | Harta / Guvernanță | PS admin drawer |
|------|---------|--------------------|-----------------|
| admin | yes | yes | yes (`view:governance`) |
| manager / sales | yes | **no** | read-only / no publication chrome |
| operator | no | no | — |

GS-12 freeze banners on `/modules` + `/governance` help **admin/owner**. Everyday Produse users need GS-11 chrome on the V2 rail.

## Issue inventory (non-cosmetic)

### I-01 ACM rail looks fully operational

- SURFACE = `/product-system/products` V2 rail
- VISIBLE_ITEM = `Alucobond casetat` under **Produse active**
- CURRENT_PRESENTATION = peer of Letters, no PARTIAL/montaj chip
- RUNTIME_TRUTH = root-offerable in policy; `/modules` ACM PARTIAL; modularity = montaj parțial
- SOURCE = `ProductSystemV2Workspace.tsx`, `activeTemplateScope.ts`, `currentTruthControlCenter.ts`
- CLASSIFICATION = ACTIVE_AND_WIRED
- Perception = AMBIGUOUS
- OWNER_CONFUSION_SCORE = 2
- OPERATIONAL_RISK = 1
- FIX_RISK = 1
- SHARED_IMPACT = 2
- RECOMMENDED_FIX_TYPE = STATUS_BADGE
- PRIORITY = P1
- Do **not** remove from rail or deactivate (that would choose authority).

### I-02 ACM display name collides with archived cassette

- SURFACE = V2 title + `humanTemplateName`
- VISIBLE_ITEM = both boxed and `TPL-ACM-CASSETTED-PANEL` map to `Alucobond casetat`
- RUNTIME_TRUTH = live code is BOXED mounting; cassette archived
- SOURCE = `productSystemAdminDisplay.ts`, `acmBoxedTemplateIdentity.ts`
- CLASSIFICATION = ACTIVE_AND_WIRED
- Perception = AMBIGUOUS
- OWNER_CONFUSION_SCORE = 2
- OPERATIONAL_RISK = 1
- FIX_RISK = 2 (name reused in Intake V6 — out of S5 if global)
- SHARED_IMPACT = 2
- RECOMMENDED_FIX_TYPE = STATUS_BADGE (PS-only chip). Global rename = OWNER_DECISION / later GO
- PRIORITY = P1

### I-03 Connection-prices card looks like live price authority

- SURFACE = Letters/ACM structure
- VISIBLE_ITEM = green **Prețuri conexiune · 20 EUR/mp**
- RUNTIME_TRUTH = owner-locked șablon, not quote authority
- SOURCE = `ProductSystemStructureReadonlyPanel.tsx:165-188`
- CLASSIFICATION = READ_ONLY_VALID
- Perception = MISLEADING
- OWNER_CONFUSION_SCORE = 2
- OPERATIONAL_RISK = 1
- FIX_RISK = 1
- SHARED_IMPACT = 2
- RECOMMENDED_FIX_TYPE = COPY_ONLY / DEMOTE (label “șablon referință · nu ofertă”)
- PRIORITY = P1

### I-04 Repo freeze missing on `/modules` and `/governance`

- SURFACE = Harta + Guvernanță
- VISIBLE_ITEM = no `CURRENT_WORKOS_FROZEN_AS_REFERENCE`
- RUNTIME_TRUTH = freeze ON (`docs/freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md`)
- SOURCE = `ModuleChain.tsx`, `Governance.tsx` — zero frontend matches
- CLASSIFICATION = READ_ONLY_VALID pages, missing status
- Perception = MISSING
- OWNER_CONFUSION_SCORE = 2
- OPERATIONAL_RISK = 0
- FIX_RISK = 1
- SHARED_IMPACT = 2
- RECOMMENDED_FIX_TYPE = FREEZE_BANNER
- PRIORITY = P1 (GS-12)

### I-05 Logo deep-link says “unknown”

- SURFACE = `/product-system/products/TPL-VOLUMETRIC-LOGO_v1`
- VISIBLE_ITEM = `Template necunoscut în listă`
- RUNTIME_TRUTH = registered candidate, root blocked
- SOURCE = `ProductSystemV2Workspace.tsx:206-212`
- CLASSIFICATION = INACTIVE
- Perception = AMBIGUOUS
- OWNER_CONFUSION_SCORE = 1
- OPERATIONAL_RISK = 0
- FIX_RISK = 1
- SHARED_IMPACT = 1
- RECOMMENDED_FIX_TYPE = STATUS_BADGE / COPY_ONLY
- PRIORITY = P2

### I-06 Spine band looks like a workflow

- SURFACE = V2 header
- VISIBLE_ITEM = 1–4 Product Template → … → Pregătire
- RUNTIME_TRUTH = non-navigational display chips
- SOURCE = `ProductSystemSpineBand.tsx`
- CLASSIFICATION = PLACEHOLDER
- Perception = AMBIGUOUS
- SCORES = 1 / 0 / 1 / 1
- RECOMMENDED_FIX_TYPE = COPY_ONLY
- PRIORITY = P2

### I-07 Next-step “Continuă spre ofertă”

- SURFACE = `ProductSystemLayout`
- VISIBLE_ITEM = commercial next-step panel
- RUNTIME_TRUTH = S1 already removed PS from FLUX; this is a hint only
- SOURCE = `commercialFlowUi.ts:118-127`
- CLASSIFICATION = ACTIVE_AND_WIRED
- Perception = AMBIGUOUS
- SCORES = 1 / 0 / 1 / 1
- RECOMMENDED_FIX_TYPE = COPY_ONLY
- PRIORITY = P2

### I-08 Governance static product nomenclator (GS-13)

- SURFACE = `/governance` tab Catalog produse (referință)
- VISIBLE_ITEM = 12 families / 50 static rows
- RUNTIME_TRUTH = not the live catalog; already `REFERINȚĂ`
- SOURCE = `Governance.tsx` ProductCatalogView + `governanceData.ts`
- CLASSIFICATION = READ_ONLY_VALID
- Perception = STALE / AMBIGUOUS
- SCORES = 1 / 0 / 1 / 1
- RECOMMENDED_FIX_TYPE = STATUS_BADGE (`STALE`) — P2, optional in S5

## Together or separate?

| | GS-11 | GS-12 |
|--|-------|-------|
| Core problem | live Produse chrome looks more operational than truth | system pages omit repo freeze |
| Who sees it | admin + manager + sales | admin only |
| Fix type | STATUS_BADGE / COPY_ONLY / DEMOTE | FREEZE_BANNER |
| Risk | low if no rename/deactivate | very low |

**Recommend one S5 implementation GO covering both**, with GS-11 as the valuable half and GS-12 as a cheap companion. Keep them as two backlog IDs. Leave GS-13 out unless owner wants the extra badge.

Do **not** implement if the owner wants ACM removed from the rail or renamed globally — that is a later decision.

## Screenshots

- [s5-ps-entry-letters.png](s5-ps-entry-letters.png)
- [s5-ps-acm-boxed.png](s5-ps-acm-boxed.png)
- [s5-ps-logo-unknown.png](s5-ps-logo-unknown.png)
- [s5-ps-planned-components.png](s5-ps-planned-components.png)
- [s5-modules-first-fold.png](s5-modules-first-fold.png)
- [s5-governance-first-fold.png](s5-governance-first-fold.png)
- [s5-governance-products-ref.png](s5-governance-products-ref.png)
