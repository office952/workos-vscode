# Remaining page dark islands (post Wave 0 shell)

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Shell day-mode | **PASS** — sidebar `rgb(255,255,255)`, `data-day-shell=true` |
| Scope of this GO | App shell chrome only — page interiors not rewritten |

## Shell verdict

| Surface | Day-mode status |
|---------|-----------------|
| Sidebar (`workos-sidebar`) | Fixed — white / light tokens |
| Topbar | Fixed — uses `--wo-surface-shell` |
| App canvas (`--wo-surface-app`) | Light grey day canvas |
| Local API compatibility banner | Intentionally dark-red warning strip (runtime diagnostic; not product chrome) |

Automated sampler on 8 representative routes under FE `:3020` found **0** large dark blocks inside `main` for those routes at capture time (many pages were empty / connecting). Code scan remains authoritative for debt.

## Remaining islands (code-backed inventory)

Count below = **page modules** under `frontend/src/pages` with ≥1 hardcoded dark utility (`bg-slate-*`, `bg-[#…]`, etc.). Standalone apps counted separately.

### In-shell product pages (Wave 1+ candidates) — **34 modules**

| Area | Modules with dark token hits | Notes |
|------|------------------------------:|-------|
| Commercial lists | Quotes, Orders, WorkIntake, IntakeDetail | Status chips / panels still night-era |
| Execution | ExecutionDetail, OperationalRealityReview, OperationalReports | Partial |
| Ops / shop | ShopFloor, TabletMode, OperatorView | Heavy slate chips |
| Registries | Inventory, DocumentCenter, Colaboratori, Attendance, … | Mixed |
| Product System | ProductSystem, BlueprintDossierStudio, OutputBlocksPreview, pricing previews | Lab chrome |
| Admin | Governance, ModuleChain, Reports, Personal | Mixed |
| People / money | EmployeeProfile, Payments, Advances, EmployeesRecords, … | Smaller hits |
| Demos | CommercialSpineDemo, VolumetricLetterPreviewDemo | DEV tooling |

### Standalone (DEFER — out of Wave 0 shell) — **3 surfaces**

| Route | Note |
|-------|------|
| `/employee-app/*` | Intentionally dark PWA shell |
| `/employee-app-v2/*` | Intentionally dark prototype |
| `/intake-v6-app/*` + in-shell Intake V6 components | Dark operator workspace; Intake V6 components not touched this GO |

### Component-layer debt (not counted in page total)

Many `frontend/src/components/workos/intake-v6/**` and `employee-mobile/**` files still use slate/hex night tokens. Track with page owners, not shell.

## Summary count for parent return

| Bucket | Count |
|--------|------:|
| Shell dark islands remaining | **0** (day mode PASS) |
| In-shell page modules with dark token hits | **34** |
| Standalone deferred dark apps | **3** |
| Runtime diagnostic banner (non-product) | **1** (LocalApiCompatibilityBanner when API mismatch) |

**Next GO suggestion:** page-by-page day-mode pass starting with Quotes / Orders / ShopFloor / Tablet (highest operator visibility), after shell is accepted.
