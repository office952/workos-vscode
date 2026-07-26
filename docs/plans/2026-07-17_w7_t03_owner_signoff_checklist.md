# W7-T03 — Owner sign-off checklist (Wave 7)

**Status:** `COMPLETE — OWNER_SIGNED` / Wave 7 `COMPLETE — OWNER_ACCEPTED`  
**Owner decision date:** 2026-07-17  
**Decision log:** D-020  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Sign-off pack HEAD:** `fc33bb8` · acceptance closure commit follows  
**Runtime:** frontend `http://127.0.0.1:3000` · backend `http://127.0.0.1:8001`

## Canonical W7-T03 definition

> W7-T03 validates that W7-T01 and W7-T02 satisfy their approved DoD, records accepted limitations, gives the owner a reproducible verification checklist, and produces a final Wave 7 sign-off decision.

No new product implementation. Evidence reconciliation + owner decision pack only.

---

## Owner decision recorded (exact)

```text
WAVE 7 = ACCEPT

W7-T01 = ACCEPT
W7-T02 = ACCEPT

LIMITARI ACCEPTATE:
- planning minutes partial = DA
- stock G3 deferred = DA
- labor cost excluded = DA
- deterministic fixture = DA
- limited template breadth = DA

DATE LOCALE DE REFERINTA:
- RETINEM

NEXT ROADMAP = GO
```

**Qualification:** Letters same-scenario spine **PROVEN_V1** — not universal system proof; not production-customer proof.

---

## Owner manual verification checklist

### Build 1 — order 92402

```text
[x] Open http://127.0.0.1:3000/execution/92402
[x] Confirm page title area shows Detaliu execuție and order #92402
[x] Confirm Observabilitate: Comandă / Plan / Realitate = prezent
[x] Confirm plan identity: plan 8 (18 operational reconciliation rows)
[x] Scroll to Post-job truth → section "Plan vs execuție"
[x] Confirm summary chips: potrivit / fără actual / total (matched=1 · missing=17 · total=18 via API)
[x] Confirm Romanian diacritics — no mojibake
[x] Confirm commercial total still 3549.1286 (UI may show 3.549,13 RON / 3549.13 RON)
```

### W7-T02 variance — order 92403

```text
[x] Open http://127.0.0.1:3000/execution/92403
[x] Confirm Observabilitate Actual ≈ 75.0 min and Δ ≈ 75.0
[x] Open "Plan vs execuție"
[x] Confirm summary: varianță: 1 · fără actual: 17 · total: 18
[x] Confirm row "Pregătire vector / font": Min. plan 0 · Min. efective 75 · Diferență 75 · stare varianță
[x] Confirm no white-screen / no mojibake
```

### Modules

```text
[x] Open http://127.0.0.1:3000/modules
[x] Tab Harta sistemelor: ExecutionPlan / Execution Reality show PROVEN_V1 same-scenario (92402 / plan 8)
[x] Tab Surse și dovezi: W7-T01 / W7-T02 / W7-T03 owner-accepted evidence
```

### Governance

```text
[x] Open http://127.0.0.1:3000/governance
[x] Tab Cine deține adevărul: ownership matrix visible (read-only)
[x] Tab Reguli de protecție → Integritate text: "UTF-8 end-to-end pentru text operator" (G13)
[x] Confirm page remains read-only (no policy editor)
```

---

## Sign-off matrix

| Area | Expected truth | Evidence | Status | Owner impact |
|------|----------------|----------|--------|--------------|
| A. Same-scenario continuity | One IR → continuous lineage | IR-BUILD1-1784237119 → WS e1b8d1e8-… → Q3 / QSN2-2026-0002 → 92402 → plan 8 | PASS | Accepted |
| B. ProductAggregate → Plan | task_contract compile | commit `ad25fa9`; plan 8 has operational tasks | PASS | Accepted |
| C. Quote/Order freeze | Snapshots frozen; total unchanged | QSN2-2026-0002 frozen; total 3549.1286; order locked | PASS | Accepted |
| D. ExecutionPlan | Plan stable after actuals | plan 8 retained | PASS | Accepted |
| E. Execution Reality | Actuals do not rewrite plan | Reality present; plan unchanged | PASS | Accepted |
| F. Post-Job | Derived / read-only | `write_back_performed=false` | PASS | Accepted |
| G. Reconciliation breadth | matched + missing + variance | 92402 / 92403 | PASS | Accepted |
| H. UI | RO Plan vs execuție; UTF-8 | Live /execution | PASS | Accepted |
| I. Modules | W7 evidence current | Surse și dovezi | PASS | Accepted |
| J. Governance | Ownership + freeze + G13 | /governance | PASS | No policy change |
| K. Limitations | TE2E-028 residuals explicit | Issue registry + below | PARTIAL_ACCEPTED | Accepted as open debt |

---

## TE2E-028 residuals (remain OPEN)

| Residual | Current truth | Wave 7 required? | Sign-off status | Next owner decision |
|----------|---------------|------------------|-----------------|---------------------|
| Planning-minute source often 0 | Mechanics work; source incomplete | No | PARTIAL_ACCEPTED | Later planning-source build |
| Stock G3 not forced | Not in W7-T02 DoD | No | PARTIAL_ACCEPTED | Inventory eligibility later |
| Labor $ excluded | Explicit exclusion | No | PARTIAL_ACCEPTED | Keep excluded |
| Deterministic fixture origin | DETERMINISTIC_LOCAL_SCENARIO | No (qualification) | PARTIAL_ACCEPTED | Fixture replacement later |
| Limited template breadth | Letters path only | No | PARTIAL_ACCEPTED | Template expansion later |

**TE2E-028 remains OPEN** — owner accepted these as limitations; do not close or hide.

---

## Freeze sign-off

| Frozen truth | Before | Current | Result |
|--------------|--------|---------|--------|
| Quote Snapshot | QSN2-2026-0002 | same · frozen | PASS |
| Quote/commercial total | 3549.1286 | 3549.1286 | PASS |
| Order | 92402 | same · locked | PASS |
| Plan | 8 | same | PASS |
| Task/ops rows (recon) | 18 | 18 | PASS |

---

## Data retention

**LOCAL_REFERENCE_DATA — DO NOT MUTATE**

Retain until deterministic automated fixture replacement **or** next release/regression baseline **or** owner-approved local DB cleanup:

| Scenario | IDs |
|----------|-----|
| Build 1 | IR-BUILD1-1784237119 · WS e1b8d1e8-0197-4723-882a-037c41c64d35 · Q3 · QSN2-2026-0002 · order 92402 · plan 8 |
| W7-T02 variance | IR-W7T02-1784238040 · order 92403 · plan 9 |

Owner decision: **RETINEM**.

---

## Next roadmap (identified, not started)

| Field | Value |
|-------|-------|
| ID | `UI-TRUTH-01B` |
| Title | Banner rendering and Romanian terminology |
| Canonical status | **PAUSED** (owner 2026-07-15) — resume candidate after Wave 7 |
| Depends | UI-TRUTH-01A COMPLETE |
| DoD clarity | Plan exists (UI-TRUTH-01); implementation DoD needs kickoff confirmation |
| Alternates | TE2E-028 residual builds · FLEX-02 (blocked until separate GO) |

Do not auto-start. Requires explicit unpause / planning prompt.
