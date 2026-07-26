# ACP Face Composition — Source Map

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_FINALIZE_BLUEPRINT_AUDIT_AND_AUDIT_ACP_COMPOSABLE_FACE_SYSTEM` |
| Owner rule | `ACP_FACE_TREATMENTS_MUST_BE_COMPOSABLE_NOT_EXCLUSIVE` |

Legend: **Y** = can represent · **P** = partial · **N** = no · **—** = N/A / out of path

---

## Source map

| Concept | Product System | SVG Analyzer | Step 1 | Step 2 | FinishSetup | PD | Aggregate | Lifecycle | CPP | Tasking |
|---------|----------------|--------------|--------|--------|-------------|----|-----------|-----------|-----|---------|
| ACP shell (cassette) | Y `TPL-ACM-BOXED…` | P contour | Y confirm | Y dimensions/fold | Y mounting_solution | Y support instance | P linked rates | Y support wiring | P boxed rates | P ops codes |
| support contour | Y `SUPPORT_CONTOUR` MAX_ONE | Y closed contour | Y | Y hydrate dims | Y bindings | Y | P | Y | — | — |
| applied letters | Y `LETTER_VECTOR_SET` → face | Y layer face | Y | Y finishes | Y letter groups | Y letter instances | Y letters path | Y | P letters | P letters |
| routed text | N (no role) | P `inner_hole`/decupat | N as ACP treatment | N | N | N | N | N | LEGACY via LIGHT-ROUTED | MISSING V6 |
| routed logo | N | P | N | N | N | N | N | N | LEGACY | MISSING V6 |
| acrylic backing / diffuser | N on boxed | N | N | N | N | N | N | N | LEGACY LIGHT-ROUTED | MISSING V6 |
| acrylic insert 10 mm | N | P `plexiInserts10mm` flag | P layer flag | N ACP config | N zone | N | N nesting hint only | N | LEGACY relief component | MISSING V6 |
| LED (ACP face cavity) | N on boxed | N | N | P letters lighting only | P letters | P letters | P letters | P | LEGACY LIGHT-ROUTED | MISSING V6 |
| electrical / PSU | N on boxed face | N | N | P cable/corner for support | P | P | P | P | LEGACY | PARTIAL letters |
| finish (panel face) | N dedicated | N | N | N stock/Oracal/RAL on ACP | N | N | N | N | LEGACY FINISAJ | — |
| internal frame | Y capability + RO | P checkbox | Y flag | Y nested config | Y | Y nested | P guarded | Y profile gate | N | N |
| fixing system | Y contract v1 | N | N | Y section | Y `mounting_fixing_system` | Y separate | P projection | P | N | N |
| service access | P corner | P contour | Y | Y corner | Y | P | P | P | — | — |
| mixed face (A+B+C+D) | **N** | **N** | **N** | **N** | **N** | **N** | **N** | **N** | **N** | **N** |
| inactive zone isolation | N | N | N | N | N | N | N | N | N | N |

---

## First failing boundary

```text
Product System SVG component-binding contract
+ FinishSetup persistence model
```

Why first:

1. No geometry roles: `CUTOUT_*`, `ROUTED_FACE`, `ACRYLIC_INSERT`.
2. `SUPPORT_CONTOUR` cardinality `MAX_ONE` — one shell, zero face-treatment attachments.
3. `LETTER_VECTOR_SET` binds to volumetric face component, **not** as treatment on ACM.
4. No `visual_zones[]` / `face_treatments[]` / `face_mode` in FinishSetup or PD.
5. Aggregate / CPP / tasking never receive mixed-face truth — failure is **upstream**.

---

## Dual product fork (secondary)

| Path | Role today |
|------|------------|
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | Live Intake V6 composition (casing + mount) |
| `TPL-ACP-LIGHT-ROUTED` | CostEngine illuminated routed product (QuoteWizard) |
| `TPL-ACM-CASSETTED-PANEL` | Candidate / future — owner_go |
| `TPL-BOND-CASETAT` | Legacy string — blocked |

Any composable-face implementation must pick **one** product authority before extending zones.

---

## Desired (not implemented) composition

```text
Panou ACP casetat (SUPPORT_CONTOUR / shell)
├── Zona A: applied volumetric letters (relation, not XOR)
├── Zona B: routed cutout + plexiglas backing + LED
├── Zona C: acrylic insert 10 mm
└── Zona D: plain / decorative
```

Dossier-inspired UI may **administer** this later; contracts + FinishSetup + PD must own the truth.
