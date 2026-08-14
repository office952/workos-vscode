# Global synthesis — consistency review (REV)

Independent of ORCH writing. Evidence: Waves 1–5 reports + contradiction log + this folder. No product code. No implementation.

| Field | Value |
|-------|--------|
| Date | 2026-08-14 |
| Baseline checked | `4018cf271cee156b8014f19c7928f7fd781cefa3` |
| Reviewer | REV |

```text
REVIEWER_VERDICT = PASS_WITH_GAPS
GAP_BLOCKS_SYNTHESIS = NO
GAP_BLOCKS_S1 = NO
```

PASS_WITH_GAPS, not CONTRADICTION_FOUND: the model holds; a few enumerations are **family-level** rather than every nested URL instance. Nothing material was silently dropped. The accepted gap does **not** block synthesis closure or the S1 plan (labels / FLUX honesty). Do not start another audit merely to make route counts exhaustive.

---

## Gate checks

| Check | Result |
|-------|--------|
| Every Wave 1–5 major finding carried / merged / superseded / retracted / deferred | YES — see disposition table in GLOBAL_SYNTHESIS_REPORT.md |
| No finding disappears silently | YES |
| No duplicate issue under multiple IDs without reason | YES — W4-C7 MERGED into C5/GS-01; W3-C1/C4 RETRACTED together |
| No projection mistaken for SoT | YES — snapshot sold; reports live; V6 preview; PD no page |
| No placeholder treated as live | YES — Documents MOCK; records DEMO; planned PS FUTURE |
| No compatibility route labeled dead without proof | YES — `/operator` `/tablet` ACTIVE_COMPAT |
| No ProductDefinition page invented | YES — OD-5 / target model |
| No 12+9 system overcount returns | YES — Level-1 = 7; U12 RETRACTED |
| No demo/mock promoted into architecture | YES |
| No cleanup without user/system value | YES — GS-23 file-only is P3; no nav delete |
| Implementation waves respect dependencies | YES — S6 blocked on OD-6; S8 last |
| No big-bang rewrite | YES |
| No owner gate bypassed | YES — IMPLEMENTATION_RECOMMENDED_NOW = NO |
| Freeze ON | YES |
| Product code / DB mutations | 0 / 0 |

---

## Wave accounting

| Wave | Accounted | Notes |
|------|-----------|-------|
| 1 | YES | Day-mode, audit-stack home, WC leak, role IA, hardcoded cards → GS-15/22 + principles |
| 2 | YES | C1–C6 all present; C6 deferred P3; C4/C5 + V6 rail = P0 |
| 3 | YES | Monitor≠action, COMPAT live, grain, unbounded list; C1/C3/C4 retractions kept |
| 4 | YES | PS/PD/PA, stale gov, freeze omit, premount DEFERRED, 12+9 retracted, PA→973024 |
| 5 | YES | MIXED RBAC deferred; suppliers SAME_TRUTH; documents/reports/records classified; SNR superseded |

Wave 3 mutating STATE_NOT_REACHED (generate/start/assign/MachineRun create) remains **DEFERRED** — correctly not turned into a simplification P0.

---

## Count audit

| Claim | Check |
|-------|--------|
| Level-1 = 7 | Matches CURRENT + TARGET models; no 12+9 |
| P0 = 3 | GS-01, GS-02, GS-03 only. Pontaj MIXED is P2 (no write hole). Visual ≠ P0. |
| TRUE_DUPLICATE = 0 | After reclass; suppliers not TRUE_DUPLICATE |
| REMOVE_CANDIDATE routes = 0 | Matches Wave 5; only file-only orphan noted |
| Route class counts | Match GLOBAL_ROUTE_CLASSIFICATION.md family table |

**Gap (kept):** classification is by **route family** (e.g. `/quotes` · `/:id` one row), not every audited deep-link instance from Wave RT logs. Acceptable for a plan; a later implementation wave must not treat an unlisted child route as unclassified-dead.

**Gap (kept):** DISPLAY_DUPLICATE (3) and COMPATIBILITY_DUPLICATE (1) exist in the reconciliation file and are omitted from the Owner final-count block (that block asked only four duplicate classes). Not a contradiction.

Independent second REV ([explore](d2d74663-6783-4d3c-a2ce-fdd85dd83983)) also flagged `/intake-v4` residue, W3-C5, and Wave 3 mutating SNR as silent. Those three are now **CARRIED / DEFERRED** in the disposition table, legacy file, duplicate matrix (D-STATUS-VOCAB), and GS-25. Residual gaps are enumeration-only.

---

## Model validation

Working three-spine model is **validated, not blindly accepted**:

- Commercial path proven Wave 2; PARTIAL journey
- Compiler proven Wave 4; PD MULTIPLE_PROXIES
- Execution proven Wave 3; Atelier ≠ action
- Lateral belt proven Wave 5; does not replace spines

Target commercial teaching (Cerere → Intake → Ofertă → Comandă) matches Wave 2 C5 / Wave 4 C7 evidence.

---

## Forbidden-scope scan

ORCH pack does not propose: implementation, cleanup, deletion, route removal, UI redesign, RBAC change, pricing change, PS/PD/PA/HR/execution feature work, migrations, DB writes, unfreeze, commit, push, PR, new PD page, new portals, new registries, new tasking systems.

S6 is explicitly **blocked** until OD-6.

---

## Residual gaps (do not block synthesis)

1. Family-level route table vs every nested URL.
2. `/clients` placement left as Owner OD-12 (correct).
3. Attendance RBAC not “fixed” in S1 (correct).
4. CHARTER Wave-gate table is historical (Wave 2+ “not authorized”) and is updated only by pointer — synthesis does not rewrite Wave 0–1 authorization history.

```text
REVIEWER_VERDICT = PASS_WITH_GAPS
GAP_BLOCKS_SYNTHESIS = NO
GAP_BLOCKS_S1 = NO
CONTRADICTION_FOUND = NO
INSUFFICIENT_EVIDENCE = NO
SYNTHESIS_MAY_CLOSE = YES
IMPLEMENTATION = STILL_NOT_AUTHORIZED
```
