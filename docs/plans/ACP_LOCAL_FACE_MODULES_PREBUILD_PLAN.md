# Pre-build plan — ACP local face modules

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Status | PLAN ONLY — awaiting owner GO + gates |
| Prerequisite | Foundation COMPLETE (`cb822da`) + this runtime review PASS |

## Single recommendation after review

**Option 1 — GO ACP BASE + LOCAL FACE MODULES TECHNICAL CONFIGURATION**

Roadmap order: modules before Dossier-inspired admin UI. Operator selection UI (Option 2) can follow once module fields exist.

## Module boundaries (no fields invented)

### Module A — Routed backlit cutout  
Binding: `CUTOUT_TEXT`/`CUTOUT_LOGO` + `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT`  
Later config (out of scope now): plexiglas backing, thickness, adhesion, diffusion, LED, PSU, wiring, service, test.  
V1 stop today: `LOCAL_CONFIGURATION_REQUIRED`.

### Module B — Acrylic insert  
Binding: `ACRYLIC_INSERT` + `FACE-TREATMENT-ACRYLIC-INSERT`  
Later config: 10 mm plexi (or options), fit, tolerance, protrusion, retention, backing, illumination.  
V1 stop today: `LOCAL_CONFIGURATION_REQUIRED`.

### Module C — Applied volumetric interface  
Binding: letters/logo external component + optional `FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT`  
Keep separate ProductDefinition instance; relation to ACP shell (position, fastening through panel, cable pass) — interface only, not absorption into shell.

## Authority (unchanged)

```text
Product System contracts → FinishSetup → ProductDefinition → (later) Aggregate → CPP → tasking
```

Dossier = admin surface only. LIGHT-ROUTED = `PARALLEL_LEGACY_COST_PATH`.

## Future Dossier-inspired Product System organization (UI only later)

```text
ACP shell
├── Structura
├── Fata și tratamente
│   ├── Routed backlit cutout
│   ├── Acrylic insert
│   └── Applied volumetric components
├── Iluminare și electric
├── Finisaje
├── Cadru interior
├── Sistem de prindere
├── Procese
└── Readiness
```

## First implementation slice (when GO)

1. Owner fills gates in `ACP_LOCAL_FACE_MODULE_OWNER_GATES.md`.
2. Typed `local_configuration` stubs on face_treatment_instances (no BOM).
3. Lifecycle: READY_FOR_AGGREGATION only when module complete.
4. Minimal operator selector (Option 2) if owner cannot use API — separate GO preferred after Module A/B stubs.

## Forbidden in next GO without explicit ask

CPP, tasking, Execution, Aggregate BOM, schema migration, seed import from LIGHT-ROUTED, Employee Mobile.
