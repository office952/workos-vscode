# Form System Runtime Capture Read Model UI E2E Coverage V1

Verdict: PASS

HEAD before implementation:
- `f2f6917`

Scope:
- add minimal E2E/smoke coverage for the existing runtime capture read-model panel in Intake V6 Review
- no new feature behavior
- no UI polish
- no Pricing change
- no DB migration/schema change
- no seed live
- no Product Truth write
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph

Infrastructure decision:
- existing Playwright infrastructure already exists under `frontend/e2e/`
- existing Intake V6 smoke exists in `frontend/e2e/intake-v6-step1-smoke.spec.ts`
- therefore this task extends the existing smoke approach instead of introducing a new framework

Coverage added:
- new Playwright smoke spec: `frontend/e2e/intake-v6-runtime-capture-read-model.spec.ts`
- assertions:
  - Review page loads
  - runtime capture panel is present
  - panel is marked read-only
  - all six runtime-capture field keys are visible
  - panel contains exactly six rows
  - no buttons, textboxes, comboboxes, inputs, textareas, selects, or contenteditable controls exist inside the panel

Verified URL / workspace:
- URL used in browser and smoke: `http://127.0.0.1:3000/intake-v6/668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c/operator`
- workspace id: `668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c`
- workspace code: `IV6-9C831ADB`

Tests run:

```powershell
cd frontend
$env:PW_SKIP_WEB_SERVER='1'
npx.cmd --yes playwright test e2e/intake-v6-runtime-capture-read-model.spec.ts
```

Result:
- `1 passed`

```powershell
cd frontend
npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/FormSystemRuntimeCaptureReadModelPanel.test.tsx
```

Result:
- `2 passed`

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_form_system_runtime_capture_read_model_endpoint.py -q
```

Result:
- `5 passed`

Browser verification:
- review page remained reachable on the verified URL
- panel was visible in Review under Form System Backbone
- screenshot captured for the runtime capture panel close-up

Files changed:
- `frontend/e2e/intake-v6-runtime-capture-read-model.spec.ts`
- `docs/worklog/realignment/2026-07-09_form_system_runtime_capture_read_model_ui_e2e_coverage_v1.md`

Opinion:
- the added smoke coverage is appropriately narrow and stable for this slice
- it checks the operator-visible contract directly without pulling Pricing, Confirm, or write flows into scope