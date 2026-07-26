# CP-F test matrix — Readiness & QA

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `705a701` |
| Agent | D — Readiness and QA |
| Aluminiu | **not activated** (inactive → BLOCKED expected) |

## Verdict

**CP-F: PASS** (static + dry_run no_write + BUILD≠PUBLICATION honesty + core suites green)

Freeze suite: 1 preexisting failure classified below — not build-caused by CP-F readiness dual-axis work.

## Static readiness

| Check | Result | Evidence |
|-------|--------|----------|
| VL static + inactive aluminiu → gate `BLOCKED` | PASS | `cp_f_readiness_no_write_evidence.json` / pytest |
| `required_inactive_child` present | PASS | known_conflicts |
| BUILD closure PASS / PASS_WITH_WARNINGS | PASS | `build_closure_status=PASS_WITH_WARNINGS` |
| TEMPLATE PUBLICATION BLOCKED | PASS | `template_publication_status=BLOCKED` |
| Aluminiu not activated | PASS | `aluminiu_activated=false` |

## Runtime dry_run no_write

| Check | Result | Evidence |
|-------|--------|----------|
| `no_write=true` / `write_performed=false` | PASS | static + runtime |
| DB sha256 before == after | PASS | `fdb45738…613d` |
| Row counts unchanged | PASS | templates=3, links=2, workspaces=0 |
| Missing workspace → runtime BLOCKED (honest) | PASS | `ws-cp-f-missing-fixture` |

Paths:

- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/cp_f_readiness_no_write_proof.py`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/cp_f_readiness_no_write_evidence.json`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/job_truth_publication_proof.py` → `PROOF_OK`

## BUILD vs TEMPLATE PUBLICATION

| Axis | Status when aluminiu inactive | Proof |
|------|-------------------------------|-------|
| BUILD closure | PASS_WITH_WARNINGS | evidence JSON + UI testids |
| TEMPLATE publication | BLOCKED | evidence JSON + publish 409 |
| Overall publish gate verdict | BLOCKED | unchanged hard gate |

**Explicit answer: yes — BUILD can PASS while TEMPLATE PUBLICATION is BLOCKED.**

## Pytest matrix

| Suite | Result | Classification |
|-------|--------|----------------|
| `test_product_e2e_readiness_v1.py` (4) | PASS | BUILD_OK |
| `test_product_template_publication_v1.py` (5) | PASS | BUILD_OK |
| `test_product_template_component_contracts_v1.py` | PASS | BUILD_OK |
| `test_product_truth_job_confirm_v1.py` | PASS | BUILD_OK |
| `test_active_scope_snapshot_freeze.py` — all except below | PASS | BUILD_OK |
| `test_v6_freeze_passes_product_truth_gate_when_confirmed` | FAIL | **PREEXISTING / OUT_OF_CP_F** — `IntakeV4WorkspacePayload` validation (`product_binding` missing, `svg_source.file_size_bytes` missing, `backing_mode='closed_back'` not in literal). Not caused by readiness dual-axis; fixture/schema drift outside allowlist surgical scope. Do not weaken. |

Combined core CP-F command: **12 passed** (readiness + publication + contracts).

Extended: **40 passed, 1 failed** (freeze case above).

## Frontend

| Suite | Result |
|-------|--------|
| `ProductE2EReadinessPanel.test.tsx` | PASS — BUILD PASS + TEMPLATE PUBLICATION BLOCKED banner |
| `ProductTemplatePublicationPanel.test.tsx` | PASS — TEMPLATE PUBLICATION BLOCKED banner |

## Semgrep

**NOT_AVAILABLE** on this host (`semgrep` not on PATH).

## Commands run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_e2e_readiness_v1.py tests/test_product_template_publication_v1.py tests/test_product_template_component_contracts_v1.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_product_e2e_readiness_v1.py tests/test_product_template_publication_v1.py tests/test_product_template_component_contracts_v1.py tests/test_product_truth_job_confirm_v1.py tests/test_active_scope_snapshot_freeze.py -q
.\.venv\Scripts\python.exe ..\docs\qa\product-system-authoring-runtime-codesign-e2e\runtime\cp_f_readiness_no_write_proof.py
.\.venv\Scripts\python.exe ..\docs\qa\product-system-authoring-runtime-codesign-e2e\runtime\job_truth_publication_proof.py

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/features/product-system/ProductE2EReadinessPanel.test.tsx src/features/product-system/ProductTemplatePublicationPanel.test.tsx
```
