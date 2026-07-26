# WorkOS Page Completion Foundation

> **WAVE 0 FOUNDATION POLICY** · **OWNER-APPROVED DIRECTION** · **NOT PAGE IMPLEMENTATION**  
> Build: **W0-B3** · GO: `GO_W0_B3_SHARED_FOUNDATION_POLICIES` · Date: 2026-07-16  
> Plan: `docs/plans/2026-07-16-workos-wave-0-foundation-truth-pages-plan.md`  
> Metadata: `docs/architecture/WORKOS_TRUTH_METADATA_CONTRACT.md` (`workos_truth_metadata/v1`)  
> Terminology: `docs/architecture/WORKOS_UI_TERMINOLOGY_REGISTRY.md`

---

## 0. Binding principle

**PAGE COMPLETION WITHOUT SYSTEM ALIGNMENT is forbidden.**

A page is **not** FINAL because it has HTTP 200, looks good, partially matches Figma, has some tests, uses real data, or shows no visible errors.

A page is FINAL only when **all** DoD dimensions below are closed **and** owner visual verification (or an explicit no-UI exception) is recorded.

This document is the shared policy for Waves 1–8 and all future page builds. It does not finalize any page and does not authorize UI/code changes by itself.

---

## 1. Page Definition of Done (mandatory)

Every page build seeking `FINAL` must satisfy **A–I**. Agents must report each section as PASS / FAIL / N/A with evidence.

### A. System identity

| Required | Notes |
|----------|-------|
| `page_id` | Stable id |
| `route` | Pattern + concrete URL used in verification |
| `system_id` | Owning system |
| Page role | ENTRY_POINT, OPERATIONAL_EDITOR, CATALOG, ADMIN, VIEWER, DOWNSTREAM_CONSUMER, TECHNICAL_INSPECTOR, DIAGNOSTIC, PREVIEW, REFERENCE, GOVERNANCE, LEGACY, HIDDEN, DEAD_CANDIDATE |
| Owner | Human/system owner reference |
| Source of truth | What this page may assert vs project |
| Upstream / downstream | Systems and pages |
| Reads / writes | Explicit; empty writes for REFERENCE |
| Contracts | Paths or contract ids |
| Dependencies | Blocking upstream builds |
| Truth metadata refs | Claim/document ids when available (W0-B1+) |

### B. Functional completeness

Real data · real API · CRUD only where permitted · validation · permissions · loading · empty · error · blocked · stale · success feedback · retry · **no dead actions** · **no simulated data presented as live**.

### C. E2E completeness

Entry · received context · primary action · persistence · confirmation · handoff · identity preservation · downstream consumer check · **no silent data loss** · **no parallel write path**.

### D. Figma completeness

| Field | Required |
|-------|----------|
| `figma_file_key` | Yes |
| Page name | Yes |
| Node ID | Yes (or NOT_FOUND after exhaustive search) |
| Flow status / approval status | Yes |
| Runtime route | Yes |
| Drift result | Classified (§3) |
| Missing states | Listed |
| Owner-approved deviation | If any |

Node existence ≠ approval. Use W0-B1 `FigmaReference` fields.

### E. UI/UX completeness

Shell · header · title · navigation · breadcrumbs · tabs · forms · tables · cards · buttons · drawers · modals · statuses · feedback · density · accessibility · consistency · responsive where relevant.

Prefer shared patterns over redesign. Intake Configurare Figma remains SoT for Intake wizard chrome. Truth pages use reference density (not ops dashboards).

### F. Language completeness

Operational UI in Romanian · registry terms · no arbitrary RO/EN mixing · technical aliases only when justified · translation keys or migration plan · validation/error messages aligned · see §5 and terminology registry.

### G. Documentation completeness

Page map · system map · contract docs · Figma refs · terminology · status · worklog · QA evidence · **truth-page impact** (§4.1) · Documentation Impact Gate classification (§4).

### H. QA completeness

Unit / integration / API / frontend tests as applicable · runtime verification · fixture · screenshots (UI) · owner verification · test DB if needed · **exact commands + results**.

### I. Delivery completeness

Isolated commit · files changed · no unrelated changes · rollback/guard · owner GO · worklog · next safe step (no auto-continue).

---

## 2. Page status rules

| Status | Meaning | Who may assign | Required evidence |
|--------|---------|----------------|-------------------|
| `READY_TO_FINALIZE` | Upstream contracts stable; Figma usable; runtime baseline known; no open OD | Build lead + review | Upstream refs, Figma ref, runtime note |
| `READY_AFTER_UPSTREAM` | Scope clear; blocked by named upstream | Build lead | Blocking build id |
| `REQUIRES_CONTRACT_FIX` | Reads/writes/ownership unclear or parallel SoT | Build lead | Contract gap description |
| `REQUIRES_FIGMA` | No approved usable flow | Build lead | Search evidence + NOT_FOUND or PARTIAL |
| `REQUIRES_RUNTIME_FIX` | Contract/code exist; runtime broken/incomplete | Build lead | Runtime URL + failure |
| `REFERENCE_ONLY` | Page is reference/read-only by design (e.g. truth pages) | Owner or OD | Role statement |
| `NO_CHANGE_NOW` | Out of current wave | Owner / plan | Wave boundary |
| `FINAL` | **Full DoD A–I + owner verification recorded** | **Owner only** (or explicit owner GO recorded in worklog) | Complete DoD checklist + evidence pack |

**Agents must not assign `FINAL`.** Proposing `READY_TO_FINALIZE` is allowed; declaring FINAL without owner verification is a policy violation.

Statuses above are **page readiness** statuses. Do not mix with system, document, Figma, or runtime vocabularies (§6).

---

## 3. Figma Flow Policy

### 3.1 Actions by flow state

| Flow state | Action |
|------------|--------|
| APPROVED | **KEEP** · **VALIDATE_RUNTIME** · **COMPLETE_MISSING_STATES** only · no full redesign without OD |
| APPROVED_WITH_NOTES | Preserve structure · resolve notes · report accepted deviations |
| PARTIAL | List missing screens/states · propose additions · owner review before implement |
| Multiple flows | Establish authority by approval + date · do not merge automatically · mark SUPERSEDED |
| NOT_FOUND | Exhaustive search first · propose using approved patterns · mark `PROPOSED — OWNER REVIEW REQUIRED` · **do not FINAL page before approval** |
| REJECTED / SUPERSEDED | Do not implement · cite replacement |

### 3.2 Runtime drift classification

| Class | Meaning |
|-------|---------|
| `RUNTIME_BUG` | Code should match Figma |
| `FIGMA_STALE` | Figma should update |
| `ACCEPTED_DEVIATION` | Owner accepted difference |
| `OWNER_DECISION_REQUIRED` | Conflict unresolved |
| `UNKNOWN` | Insufficient evidence |

### 3.3 Mandatory Figma evidence fields

`figma_file_key` · page · node · flow · approval · last reviewed · runtime route · screenshots/evidence where applicable · supersession node ids when replaced.

Known anchors (keep; do not reinvent):

- MASTER: `911Q6oRKcEursrRoT4Qj0h` (e.g. nodes `14:2`–`14:15`)
- Intake Configurare: `0CDPIuqoaZ1OQgNnvNyl1F`

---

## 4. Documentation Impact Gate

### 4.1 Questions (all applicable must be answered)

1. System ownership changed?  
2. Contract changed?  
3. Writer or reader changed?  
4. Route changed?  
5. Page role changed?  
6. Figma flow changed?  
7. UI changed?  
8. Terminology changed?  
9. Status changed?  
10. Dependency changed?  
11. Freeze boundary changed?  
12. Runtime behavior changed?  
13. Claim superseded?  
14. New evidence produced?  
15. Which truth pages affected? (Harta / Guvernanță / Centru)

### 4.2 Classification (pick all that apply)

`NO_DOC_IMPACT` · `WORKLOG_ONLY` · `STATUS_UPDATE` · `PAGE_MAP_UPDATE` · `SYSTEM_MAP_UPDATE` · `CONTRACT_DOC_UPDATE` · `FIGMA_REFERENCE_UPDATE` · `TERMINOLOGY_UPDATE` · `TRUTH_METADATA_UPDATE` · `GOVERNANCE_UPDATE` · `CANONICAL_ARCHITECTURE_UPDATE` · `OWNER_DECISION_REQUIRED`

### 4.3 Closure rule

A build cannot receive **`COMPLETE`** until documentation impact is **assessed**, **classified**, **applied where allowed**, and **owner-gated** where required (`CANONICAL_ARCHITECTURE_UPDATE`, `OWNER_DECISION_REQUIRED`, archive/replace).

### 4.4 Truth-page impact (mandatory even before truth pages mature)

| Truth page | Report if build changes |
|------------|-------------------------|
| **Harta sistemelor** | systems, pages, edges, contracts, handoffs, providers, consumers, freeze points, runtime checks |
| **Guvernanța sistemului** | ownership, writers/readers, forbidden rules, owner gates, authority, statuses, boundaries |
| **Centrul de documentație** | document relationships, status, authority, validation, Figma/code/test/worklog refs, supersession |

Report `NONE` explicitly when no impact.

---

## 5. Romanian-first UI Policy

**Operational UI language = Romanian.**

| Allowed English | Forbidden |
|-----------------|-----------|
| Code identifiers, API fields, logs, debug panels, file paths | Random mixed navigation |
| Technical acronyms with justification | English status beside Romanian status for the same concept |
| Confirmed product/brand names (owner-gated) | Duplicate per-page translations |
| Secondary `technical_alias` | Technical model names as default operator labels without reason |
| | Per-component improvisation outside registry |

### Display model (align with W0-B1)

```text
display_label_ro
technical_alias
translation_key
description_ro
```

Example: `display_label_ro: "Harta sistemelor"` · `technical_alias: "Module Chain"` · `translation_key: "system_map.title"`

**This policy does not change UI strings.** String migration requires a separate GO.

Registry: `docs/architecture/WORKOS_UI_TERMINOLOGY_REGISTRY.md`.

---

## 6. Status vocabularies (separated)

Do **not** mix categories. One entity may carry multiple category statuses (e.g. page readiness + runtime).

### 6.1 System

`OPERATIONAL` · `OPERATIONAL_PARTIAL` · `PREVIEW_ONLY` · `REFERENCE_ONLY` · `STATIC` · `BLOCKED` · `LEGACY` · `UNKNOWN`

| Assign by | Evidence | Revalidate when |
|-----------|----------|-----------------|
| System owner / OD + runtime proof for OPERATIONAL* | Code + tests + runtime | Contract or freeze change |

### 6.2 Page readiness

See §2. Assign by build lead except `FINAL` (owner).

### 6.3 Document

`CANONICAL_CURRENT` · `SUPPORTING_CURRENT` · `RECENT_EVIDENCE` · `DIRECTION_ONLY` · `REFERENCE` · `STALE` · `SUPERSEDED` · `CONTRADICTORY` · `OWNER_REVIEW_REQUIRED`

| Assign by | Evidence |
|-----------|----------|
| Doc owner / OD for CANONICAL_* | Authority ladder + validation date |

Allowlisted path ≠ canonical (W0-B1 rule).

### 6.4 Figma

`APPROVED` · `APPROVED_WITH_NOTES` · `PARTIAL` · `PROPOSED` · `EXPLORATORY` · `REJECTED` · `SUPERSEDED` · `NOT_FOUND`

| Assign by | Evidence |
|-----------|----------|
| Owner / Figma review pack | Node + review date; never infer from node existence |

### 6.5 Runtime

`VERIFIED` · `VERIFIED_WITH_GUARDS` · `PARTIAL` · `DEGRADED` · `BLOCKED` · `NOT_CHECKED` · `UNKNOWN`

| Assign by | Evidence |
|-----------|----------|
| Build lead from runtime session | URL, timestamp, result; TTL / recheck on related change |

**Runtime never proves approved architecture** (binding; see truth metadata contract).

---

## 7. i18n preparation policy (no framework in this build)

Repo check (2026-07-16): **no** `i18n` / `react-intl` / `i18next` in frontend `package.json`.

| Decision | Policy |
|----------|--------|
| Default locale | `ro` |
| Fallback | Missing key → Romanian string from registry → last-resort technical EN |
| Key naming | Dotted snake_case, ≥2 segments (`system_map.title`) — matches W0-B1 |
| Namespaces | Prefer domain prefixes: `nav.*`, `system.*`, `status.*`, `action.*`, `error.*`, `truth.*` |
| Technical identifiers | Never translate `TPL-*`, UUIDs, API field names |
| Backend errors | Map known codes to RO at API/UI boundary; raw detail in debug |
| Status labels | From registry; same term everywhere |
| Pluralization / dates / currency | Defer to i18n GO; until then use consistent RO formatting helpers if already present |
| Migration | Gradual: registry → nav → statuses → CTAs → bodies |
| Constraint | **Never** mix translation with contract/behavior changes |
| Implementation | Requires separate **G-W0-I18N** |

---

## 8. Owner visual verification standard

### UI builds — required report fields

exact URL · route · page · tab/section · fixture ID · prerequisites · click steps · expected title · expected status · expected button/action · expected data · expected warning · expected empty/loading/error · Figma node · screenshot evidence

### Non-UI builds

State explicitly:

`NO VISUAL VERIFICATION REQUIRED`

and provide schema/test/import verification paths instead.

---

## 9. QA and evidence standard

### Evidence classes

`CODE` · `TEST` · `API` · `DB` · `RUNTIME` · `FIGMA` · `SCREENSHOT` · `WORKLOG` · `OWNER_DECISION` · `CANONICAL_DOCUMENT`

### Each evidence item must include

exact path · command · result · timestamp · fixture · environment · status · limitations

### Prohibited phrases without evidence

- “tested successfully” without command  
- “runtime works” without URL/evidence  
- “aligned with Figma” without node  
- “documented” without path  

---

## 10. Worklog standard

Every build worklog must include:

build ID · owner GO · date · branch · HEAD before/after · working tree before/after · objective · sources read · research · changes · files · contracts · pages · systems · tests · runtime · Figma · terminology · documentation impact · truth-page impact · risks · blockers · commit · rollback · next safe step · roadmap score · direction score

Location convention: `docs/worklog/realignment/` (or feature worklog path stated in GO).

---

## 11. Commit standard

| Rule | Requirement |
|------|-------------|
| Objective | One coherent operational objective |
| Isolation | No unrelated files |
| Tests | Run before commit when code touched |
| Worklog | Updated in same commit or immediately after with hash in report |
| Staging | Exact staged file list in report |
| Hash | Reported |
| Continuation | **No automatic next build** |

Docs-only commits allowed when GO authorizes documentation scope (this build).

---

## 12. Multitasking policy

```text
RESEARCH IN PARALLEL.
DECISION CENTRALIZED.
IMPLEMENTATION CONTROLLED.
```

**Parallel OK:** documentation research · Figma inventory · route inventory · FE/BE tracing · runtime verification · terminology scans · QA analysis  

**Do not parallelize conflicting writes to:** shared contracts · same page · same schema · same canonical document · same Figma flow  

Orchestrator reconciles findings before write.

---

## 13. Template integration (reference targets)

Future prompts and checklists should cite this document. **B3 updates only AGENTS.md pointer** (docs). Later GOs may update:

| Location | Role |
|----------|------|
| `AGENTS.md` | Agent entry pointer (§ Build discipline) |
| `docs/qa/BUILD_*.md` templates | Purpose / boundary / commands sections |
| Worklog template (realignment) | Impact + truth-page sections |
| Code review / doc review checklists | DoD + Doc Impact Gate |
| Page finalization prompts | Full DoD A–I |

No CI enforcement in B3.

---

## 14. Relationship to other Wave 0 artifacts

| Artifact | Relation |
|----------|----------|
| W0-B1 Truth Metadata | Executable claim/Figma/document schemas; this policy defines when to use them |
| Wave 0 plan | Sequencing; B3 implements plan §8 policies as binding foundation |
| Page/System/Figma study | Analysis input; not superseded as study, but DoD/policies here are binding for completion |
| Terminology registry | Binding registry model + seed recommendations |

---

## 15. Forbidden misuse

- Declaring pages FINAL under this GO  
- Using policies to justify UI translation without GO  
- Treating HTTP 200 as DoD  
- Promoting runtime health to architecture approval  
- Starting W0-B2/B4–B8 under this GO  
