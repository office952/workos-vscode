# Plan — Product System Blueprint reuse recommendation

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_AUDIT_HISTORICAL_PRODUCT_SYSTEM_BLUEPRINT_UI` |
| Status | **RECOMMENDATION ONLY** — awaiting owner review |
| Audit | `docs/audits/2026-07-18_product_system_blueprint_historical_ui_audit.md` |

---

## Single recommendation

### Option 2 — REUSE BLUEPRINT VISUAL PATTERNS INSIDE CURRENT PRODUCT SYSTEM UI

Port the **information architecture and section-group clarity** from:

- Product System IA shell (`3be9c72` — Products / Components / Dossiers / Guards / …)
- Blueprint Dossier Studio authority-grouped sections

…into the **current** Product System shell and detail experience, while keeping:

- Product System contracts as technical authority
- Blueprint Dossier as documentation admin (already live)
- Aggregate / existing tasking as compile + runtime

**Do not** invent or restore a React Flow canvas (never in git history).  
**Do not** treat dossier `task_rules` as a task engine.

---

## Why not the other options

| Option | Why rejected as primary |
|--------|-------------------------|
| **1 — Restore Blueprint UI as admin surface** | Already largely true (Studio + API live). Framing as “restore lost canvas” invents history. Discovery/IA polish ≠ full restore project. |
| **3 — Keep current UI; port only finish/task concepts** | Under-delivers on owner clarity ask (components / materials / ops / deps overview). Finish concepts are not primarily in Blueprint. |
| **4 — Do not reuse** | Too strong — Studio is real, useful documentation admin; IA patterns were good. |

---

## Evidence summary

| Evidence | Supports Option 2 |
|----------|-------------------|
| Blueprint Dossier Studio still at `/product-system/blueprint-dossier` | Surface exists — improve placement + patterns |
| IA tabs screenshot `07_dossiers_tab.png` / commit `3be9c72` | Recoverable hierarchy |
| Unified/canonical collapse (`0eb5088`, `5c6b4e4`) | Explains perceived “loss” |
| No reactflow/@xyflow ever in package.json history | Blocks Option 1-as-canvas |
| TaskRulesEditor banners forbid task creation | Safe reuse boundary |
| ACP mixed-face not in dossier | ACP full audit remains separate next step |

---

## Integration boundaries (if owner GO follows)

**In:**

- Navigation / overview composition
- Authority-labeled section groups in Product System detail
- Deeper link / discoverability of Blueprint Dossier
- Read-only visualization of contracts (components, RO, process intent, declared task rules)

**Out:**

- New persistence schema for “Blueprint graph”
- Parallel task/workflow engines
- Pricing / CPP activation
- Execution / Employee Mobile
- Copy-paste of orphan `DossierCompletionDashboard` as second readiness SoT

---

## Estimated cost / risk

| Factor | Assessment |
|--------|------------|
| Integration cost | Medium — mostly FE IA over existing APIs |
| Authority risk | Low if banners + Aggregate path preserved |
| Nostalgia risk | Medium — must not rebuild empty planned stubs as fake operational pages |
| ACP readiness | Unblocked later; Blueprint reuse does not solve multi-face ACP |

---

## Owner gates before implementation

1. Confirm Option 2 (vs stop).
2. Confirm Blueprint Dossier remains documentation admin (not product SoT).
3. Confirm no React Flow / canvas GO.
4. Confirm planned shell sections stay honest (“Planificat”) until contracts wire them.

---

## Next safe step (single)

**STOP FOR OWNER UI REVIEW**

Alternate if owner already agrees: `GO PORT BLUEPRINT PATTERNS INTO CURRENT UI`.  
Not recommended yet: `GO RESTORE BLUEPRINT ADMIN SURFACE` (misleading), `GO ACP FULL SYSTEM AUDIT` (can wait until UI direction chosen).
