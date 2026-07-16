# GRADI-CURAT DOSSIER + TRIGGER — FINAL OWNER REPORT (29 sections)

**Task:** `WORKOS-GRADI-CURAT-DOSSIER-AND-TRIGGER-TRUTH-AUDIT-V1`  
**Date:** 2026-07-16  
**Worktree:** `C:\w\psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `c6302b9e30eb04a4a80aa82f16ce76c0ecb4dd84`  
**Mode:** Docs-only audit artifacts (no product / severity-mapping implementation)  
**Workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Operator route:** `http://127.0.0.1:3000/intake-v6/11891d68-c4c8-4719-acc5-f8fcb22a44af/operator`

---

## 1. Verdict

| Field | Value |
|-------|-------|
| Classification | `READY_FOR_QUOTE_BUT_NOT_EXECUTION` |
| Can operator confirm and continue? | `YES_FOR_QUOTE_ONLY` |
| First coherent blocker (dossier track) | `UI_SEVERITY_MAPPING` |
| Audit proof token | `GRADI_CURAT_DOSSIER_TRIGGER_TRUTH_PROVEN` |
| Implementation in this task | **NO** |

---

## 2. Repository truth

- Protected CostEngine / Pricing / Inventory / QuoteWizard handoff paths: **not modified**
- Product System dossier rewrite: **not performed**
- Severity-mapping code: **not changed** (correction boundary documented only)
- Dirty unrelated worktree files may exist; this task writes **docs/evidence only**

---

## 3. Runtime truth (audit-time reads)

| Surface | Value |
|---------|-------|
| Backend | `http://127.0.0.1:8001` (reused) |
| Frontend | `http://127.0.0.1:3000` (reused) |
| Canonical handoff read | `GET /api/v1/intake-v6/workspaces/{id}/quote-handoff-preview` |
| Commercial read | `GET .../priced-quote-dry-run` → `V6_PRICED_DRY_RUN_READY` |
| Auth | `Bearer __DEV_BYPASS_TOKEN__` (dev bypass) |
| Workspace / pricing / DB writes in this task | **NONE** |

---

## 4. Workspace / composition truth

| Field | Value |
|-------|-------|
| Root template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Linked composition | Vector Logo children (N logos) commercially bound |
| Mounting | `mounting_solution.kind=installation_template` + `mounting_scope=preparation_and_site_installation` |
| `finish_setup.mounting_system` | empty (premount metal path not selected) |
| Site install commercial | 1× `SITE_INSTALLATION_STANDARD` → 1000 RON |
| Quote | `quote_exists=false` |

---

## 5. Live commercial non-regression

| Metric | Value |
|--------|--------|
| Dry-run | `V6_PRICED_DRY_RUN_READY` |
| Net | **3513.56** RON |
| VAT 21% | **737.85** RON |
| Gross | **4251.41** RON |
| Montaj | 1 line |
| Logo commercial lines | present (N logos, generic) |

Dossier/trigger codes do **not** invalidate CPP/dry-run totals.

---

## 6. Live code inventory (handoff)

| Bucket | Codes |
|--------|-------|
| `fatal_blockers` (only) | `operator_confirmation_missing` |
| `review_warnings` (5) | 2× `TRIGGER_FIELD_MISMATCH`, `DOSSIER_METADATA_ONLY`, `CANONICAL_CONTRACT_AUTHORITY`, `TEMPLATE_IDENTITY` (each prefixed `canonical_unresolved_warning:`) |

Legacy `blockers[]` = fatal ∪ review (UI inflation only).

---

## 7. Exact stage matrix (current runtime)

Legend: BLOCK = hard reject; ALLOW = proceeds; \* = after Step 3 operator confirmation clears the only fatal.

| Code | Quote draft | Priced offer | Offer accept | Order convert | Execution plan |
|------|-------------|--------------|--------------|---------------|----------------|
| `operator_confirmation_missing` | **BLOCK** | **BLOCK** | BLOCK (precondition) | BLOCK | BLOCK |
| `TRIGGER_FIELD_MISMATCH` (form) | ALLOW | ALLOW* | **BLOCK** | **BLOCK** | **BLOCK** |
| `TRIGGER_FIELD_MISMATCH` (Aggregate) | ALLOW | ALLOW* | **BLOCK** | **BLOCK** | **BLOCK** |
| `DOSSIER_METADATA_ONLY` | ALLOW | ALLOW* | **BLOCK** | **BLOCK** | **BLOCK** |
| `CANONICAL_CONTRACT_AUTHORITY` | ALLOW | ALLOW* | **BLOCK** | **BLOCK** | **BLOCK** |
| `TEMPLATE_IDENTITY` | ALLOW | ALLOW* | **BLOCK** | **BLOCK** | **BLOCK** |

Precision: dossier/trigger codes are **not** in `fatal_blockers`. Draft + priced-offer create check fatals / dry-run READY only. Accept/convert/production use `client_order_production_flags_for_quote(review_warnings)` — any non-empty list clears all four flags.

---

## 8. Per-code truth

| Code | Source | Current severity | Handoff bucket | Intended lifecycle | Quote | Order/Execution |
|------|--------|------------------|----------------|-------------------|-------|-----------------|
| `operator_confirmation_missing` | `list_v4_handoff_issue_codes` → `finish_setup.internal_draft_quote_confirmed` | Fatal | `fatal_blockers` | Legitimate Step 3 gate | Block until checkbox | Keep |
| `TRIGGER_FIELD_MISMATCH` (form) | `TRIGGER_ALIGNMENTS` in modular form contract → PD unresolved | Diagnostic string | `review_warnings` | Review until link migrates or equivalent truth accepted | Never block Quote | May remain Order/Execution review |
| `TRIGGER_FIELD_MISMATCH` (Aggregate) | `TRIGGER_FIELD_MISMATCHES` map `metal_support_required`→`mounting_system` | Aggregate `warning` | `review_warnings` | Same (duplicate of form row) | Never block Quote | Same |
| `DOSSIER_METADATA_ONLY` | Aggregate when blueprint row exists | Aggregate **`info`** | `review_warnings` | Metadata/diagnostic forever | Never block | **Should never block** |
| `CANONICAL_CONTRACT_AUTHORITY` | Aggregate when canonical contract exists | Aggregate **`info`** | `review_warnings` | Authority trace | Never block | Never block |
| `TEMPLATE_IDENTITY` | Aggregate identity resolution | Aggregate **`info`** | `review_warnings` | Identity trace | Never block | Never block |

---

## 9. Operator confirmation (accepted — out of re-analysis)

- Code: `operator_confirmation_missing`
- Field: `finish_setup.internal_draft_quote_confirmed`
- Emitter: `intake_v4_internal_draft_quote_policy_service.py` → V6 re-export
- Cleared only by Confirm checkbox → `PUT .../internal-draft-quote-confirmation`
- Step 1/2 do **not** replace it; finish/composition/layer saves **reset** it
- **Do not** remove, bypass, or auto-confirm
- Proved independent: only code in `fatal_blockers` today

---

## 10. Dossier truth

| Question | Answer |
|----------|--------|
| Which dossier | Root `TPL-VOLUMETRIC-LETTERS_v2` blueprint via Aggregate `_load_dossier` |
| Root vs linked child | **Root only** — not emitted per Vector Logo segment |
| Version/status | dossier_version **3**, status **approved** |
| Class | `INFORMATIONAL_METADATA_WARNING` |
| Metadata-only meaning | By design: dossier is inspection; runtime authority = canonical template contracts |
| PD / PA / CPP | Still compile/evaluate (dry-run READY) |
| ExecutionPlan | **Not** missing operational truth from this info code; production blocked only via review_warning lift |

---

## 11. Trigger mismatch truth

| Trigger | Module | Expected | Actual | Equivalent truth | Impact |
|---------|--------|----------|--------|------------------|--------|
| premount optional | `structura_suport` / metal premount link | `finish_setup.mounting_system` | link `metal_support_required` | Yes — `mounting_solution` + `mounting_scope`; site install priced | Commercial OK; alias drift |

Cause: **legacy alias / renamed Intake field** (documented OPEN), not missing value for this composition.  
ACM boxed path (`mounting_solution_active`) — not in this payload.  
Sources: `TRIGGER_ALIGNMENTS` in `intake_v6_modular_form_contract_service.py`; Aggregate `TRIGGER_FIELD_MISMATCHES` in `product_aggregate_service.py`.

---

## 12. Root vs linked-child

| Surface | Finding |
|---------|---------|
| Root volumetric letters | Owns all 5 review_warning codes |
| Vector Logo children (0..N) | **No** separate dossier/trigger handoff codes; commercial lines bound |
| Site install | Commercial montaj OK; TRIGGER concerns optional premount metal, not `SITE_INSTALLATION_STANDARD` |

---

## 13. Quote readiness

After Step 3 operator confirmation (fatal cleared; review_warnings remain):

| Check | Result |
|-------|--------|
| Commercial (CPP / dry-run) | Ready now |
| Quote draft create | **Allowed** (fatal-only gate) |
| Priced offer create | **Allowed** (draft + dry-run READY); may set `requires_pricing_review=true` |
| Dossier/trigger invalidate commercial? | **No** |

---

## 14. Order readiness

| Check | Result |
|-------|--------|
| Current runtime | **Blocked** while any `review_warnings` remain (`accept_allowed` / `convert_to_order_allowed` false) |
| Over-broad? | **Yes** — Aggregate `info` traces should not block Order |
| Intended | Info traces never block; TRIGGER may remain Order review until migration or equivalent-truth acceptance |

---

## 15. Execution readiness

| Check | Result |
|-------|--------|
| Current runtime | **Blocked** (`production_allowed=false` via same review_warnings mechanism) |
| Cause | Severity lift — **not** “dossier body missing” |
| Intended | Keep execution gated where operational truth incomplete; do not use info metadata as that gate |

---

## 16. Exact severity-mapping defect

```text
Aggregate severity=info|warning  +  form TRIGGER_ALIGNMENTS
        ↓
PD validation.unresolved_warnings  (all codes, no severity filter)
        ↓
canonical_unresolved_warning:*  →  review_warnings
        ↓
accept_allowed = convert = production = false   if review_warnings non-empty
```

Key files:

- `backend/services/product_aggregate_service.py` — emit info/warning conflicts
- `backend/services/product_definition_builder_service.py` — lift all Aggregate warnings to unresolved
- `backend/services/intake_v6_canonical_readiness_service.py` — `collect_canonical_readiness_findings` / `merge_policy_findings`
- `backend/services/intake_v4_internal_draft_quote_policy_service.py` — `client_order_production_flags_for_quote`
- `backend/services/intake_v6_commercial_quote_service.py` — draft create fatal-only

**Not** promoted into `fatal_blockers` for draft.  
**Yes** promoted to Order/Execution blockers via review channel.

---

## 17. Intended lifecycle (owner direction — move, do not delete)

| Code | Intended boundary |
|------|-------------------|
| `operator_confirmation_missing` | Keep Step 3 fatal |
| `DOSSIER_METADATA_ONLY` | Diagnostic forever; never block Quote/Order/Execution |
| `CANONICAL_CONTRACT_AUTHORITY` | Diagnostic; never block |
| `TEMPLATE_IDENTITY` | Diagnostic; never block |
| `TRIGGER_FIELD_MISMATCH` | Never block Quote; remain Order/Execution review until link migration or owner accepts equivalent Intake truth |

---

## 18. One coherent correction boundary (next phase — not this task)

**Name:** `UI_SEVERITY_MAPPING` / readiness channel split

**Include:**

- Do **not** promote Aggregate `severity=info` into handoff `review_warnings` that clear `accept_allowed`
- Keep diagnostics visible (separate diagnostic channel or non-gating bucket)
- Route TRIGGER explicitly as Order/Execution review (not silent global nonblock)
- Never auto-confirm; never bypass PD/PA; never change pricing

**Stop when:** info traces no longer block accept/convert; TRIGGER disposition decided once; commercial totals stable.

---

## 19. Tests required (for later GO)

1. Aggregate `info` codes do not clear `accept_allowed` by themselves
2. `operator_confirmation_missing` still fatal for draft when unchecked
3. TRIGGER disposition explicit (blocks Order/Execution or not per owner gate)
4. Dry-run totals unchanged (3513.56 / 737.85 / 4251.41 non-regression)

---

## 20. Runtime proof required (for later GO)

1. After operator confirm → draft + priced offer OK
2. Accept/convert/production flags match intended matrix
3. Diagnostics still visible in handoff/UI
4. No workspace/pricing/registry mutation beyond operator confirm checkbox

---

## 21. Owner gates (before correction GO)

1. Confirm Quote may proceed after Step 3 confirm despite dossier/trigger diagnostics (`YES_FOR_QUOTE_ONLY`).
2. Confirm Order/Execution blocking set: **TRIGGER only** (recommended) vs none until Product System link work.
3. Confirm Aggregate `info` traces stay **visible but non-blocking** post-Quote.

---

## 22. Forbidden scope (held)

- Suppress or delete diagnostics
- Make all warnings nonblocking globally
- Bypass ProductDefinition / ProductAggregate truth
- Auto-confirm / remove Step 3 gate
- Product System dossier rewrite / invent dossier body
- Pricing / registry / CostEngine changes
- Quote/Order creation in this audit
- Workspace / DB writes in this audit
- Commit until owner review; push/PR: **NO/NO**
- Edit Cursor plan file

---

## 23. Evidence package

| Artifact | Path |
|----------|------|
| This report | `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/plan.md` |
| Decision log | `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/decision-log.md` |
| Worklog | `docs/worklog/realignment/2026-07-16_gradi_curat_dossier_trigger_truth_audit.md` |
| Evidence JSON | `docs/qa/gradi-curat-e2e/dossier-trigger-truth-evidence.json` |

---

## 24. Runtime writes performed (this task)

**NONE** — docs-only.

---

## 25. Cleanup result

N/A — no workspace side effects.

---

## 26. Commit / Push / PR

| Action | Status |
|--------|--------|
| Commit | **NO until owner review** |
| Push | **NO** |
| PR | **NO** |

---

## 27. Honest opinion

Do not delete warnings — move them to the correct lifecycle stage. Quote after operator confirm is commercially sound. Blocking Order/Execution on `DOSSIER_METADATA_ONLY` / identity traces is false friction. TRIGGER is the only candidate that might still belong on the Order/Execution boundary until Product System cleans the link field.

---

## 28. Roadmap awareness checkpoint

| Item | Value |
|------|--------|
| Score | 8/10 |
| Position | Post commercial + operator-gate clarity; pre accept/convert hygiene |
| Dead pieces | Info codes as commercial blockers are false friction |
| Forbidden held | Docs-only; no product implementation |
| Directia stabilita | ~90% |

---

## 29. Recommended next action

1. Owner answers gates G1–G3 (section 21)
2. Docs-only commit after owner review (no push/PR)
3. Separate GO for severity-mapping correction only — keep operator confirmation gate intact
