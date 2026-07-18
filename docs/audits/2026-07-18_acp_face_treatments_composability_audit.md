# Audit — ACP face treatments composability

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_FINALIZE_BLUEPRINT_AUDIT_AND_AUDIT_ACP_COMPOSABLE_FACE_SYSTEM` |
| Owner rule | `ACP_FACE_TREATMENTS_MUST_BE_COMPOSABLE_NOT_EXCLUSIVE` |
| Mode | Audit only |

---

## Verdict

**MIXED_FACE_NOT_REPRESENTABLE — FIRST_FAIL_AT_SVG_BINDING_AND_FINISHSETUP**

Live system supports **one** Alucobond boxed shell + separate letter/logo product bindings. It does **not** support simultaneous Zones A–D as face treatments on the same ACP panel. There is no exclusive global `face_mode` enum either — the gap is **missing composability**, not a wrong exclusive mode.

---

## Owner use case

```text
Panou ACP casetat
├── Zona A: litere volumetrice aplicate
├── Zona B: text decupat CNC + plexiglas spate + LED
├── Zona C: logo insert plexiglas 10 mm
└── Zona D: față plină / decorativă
```

---

## Layer matrix

| Layer | Poate reprezenta? | Cum | Ce lipsește | Primul failure |
|-------|-------------------|-----|-------------|----------------|
| Product System | Partial shell only | `TPL-ACM-BOXED…` + `SUPPORT_CONTOUR` | Face treatment modules/roles | Binding contract |
| SVG Analyzer | Partial | Contour + letter layers + `plexiInserts10mm` flag + `inner_hole` heuristic | CUTOUT/INSERT/ROUTED roles; zone identity | Role inventory |
| Intake Step 1 | Partial composition | Letters + one support contour | Multiple treatments on panel face | Same |
| Intake Step 2 | Shell + frame + fixing | Global panel fields | Routed/insert/LED zone config | Step 2 schema |
| FinishSetup | Bindings + mounting_solution | No zone array | `face_treatments[]` | FinishSetup model |
| ProductDefinition | `svg_component_instances` | Product instances only | Zone treatments + provenance | PD canonical model |
| ProductAggregate | Letters + ACM rates | No zone projection | Combined zone BOM without duplicates | Downstream of PD |
| Lifecycle | Support/letter wiring | No per-zone readiness | Zone incomplete vs shell complete | Downstream |
| CPP | Boxed rates / LIGHT-ROUTED legacy | No mixed-face | Zone rules | Downstream |
| Task preview | Boxed ops / letters ops | No zone tasks | Routed/insert/assembly | Downstream |

---

## Role inventory (real only)

| Role | Exists | Definition | Producer | Consumer | Treatment implied | Conflict |
|------|--------|------------|----------|----------|-------------------|----------|
| `LETTER_VECTOR_SET` | Y | Letter geometry set | Analyzer / Step 1 | Face component | Applied letters product | Not ACP face treatment |
| `LOGO_VECTOR_SET` | Y | Logo geometry | Step 1 | Logo component (guarded) | Logo product | Same |
| `SUPPORT_CONTOUR` | Y | Outer support contour | Contour confirm | ACM boxed `MAX_ONE` | Shell only | vs contour/layer names |
| `DECORATIVE_VECTOR` | Y listed | Decorative | — | **Unbound** | None | Dead binding |
| `IGNORE` | Y listed | Ignore | — | **Unbound** | None | — |
| `CUTOUT_TEXT` | **N** | — | — | — | — | Missing |
| `CUTOUT_LOGO` | **N** | — | — | — | — | Missing |
| `ROUTED_FACE` | **N** | — | — | — | — | Missing (`FATA_ACP_ROUTATA` is CostEngine type) |
| `ACRYLIC_INSERT` | **N** | — | — | — | — | Missing (`plexiInserts10mm` is layer flag) |

Contour roles (separate vocabulary): `ALUCOBOND_CASED_PANEL`, `FLAT_BACKGROUND`, `DECORATIVE_CONTOUR`, `GRAPHIC_ELEMENT`, `IGNORE`.

Layer auto-roles (separate): `face`, `support_panel`, `inner_hole`, `printed_artwork`, …

---

## Global mode vs composable zones (code-based)

| Criteriu | Global `face_mode` | Composable treatments/zones |
|----------|--------------------|-----------------------------|
| Litere + routed text | Would force XOR product | Required by owner; **not implemented** |
| Routed + insert | Would force XOR | Required; **not implemented** |
| Geometry provenance | Single mode loses multi-zone identity | Needs zone_id + geometry identity |
| Finish per zone | Impossible under one finish enum | Needs treatment ≠ finish |
| Process projection | One process graph per mode | Per-zone process + shared shell |
| Inactive isolation | Hide whole product mode | Per-zone inactive |
| UI clarity | Simpler but false | Harder; Dossier groups help |
| Compatibility | Fits LIGHT-ROUTED exclusive components | Fits component-bindable pattern **after** authority fix |
| Migration risk | Lower short-term, wrong truth | Higher, correct truth |

**Decision from code:** do not introduce exclusive `face_mode`. Prefer composable treatments **after** fixing binding/persistence authority (see recommendation doc).

---

## Finish vs treatment vs material

| Concept | Meaning | ACP live path |
|---------|---------|---------------|
| Finish | Surface appearance (stock color, Oracal, RAL, paint) | **Missing** on ACM boxed; letters own Oracal/RAL |
| Treatment | Construction (full face, routed cutout, insert, applied letters) | **Missing** as first-class; collapsed into shell vs other products |
| Material | Resource (ACM sheet, plexi 10 mm, LED) | ACM thickness on shell; plexi/LED not on shell |
| Geometry role | Intent for binding | Only LETTER/LOGO/SUPPORT (+ unbound decorative/ignore) |

Do **not** merge these into one enum.

---

## Step 1 model shape

| Question | Answer |
|----------|--------|
| Global / per-layer / per-zone? | **Fragmented:** per-layer for letters/logo; **global** for ACP shell; **no** per-zone treatments |
| Multiple treatments simultaneous? | Only as separate products (letters + one support), not face zones |
| Hidden ACP injection / synthetic ids? | Early support association exists; must not invent zone ids |

## Step 2 coexistence

| Config | Exists | Coexists without override? |
|--------|--------|----------------------------|
| ACP shell (thickness, fold, returns, back lip) | Y | Y (global) |
| Internal frame | Y | Y (nested) |
| Fixing system | Y | Y (separate) |
| Routed backlit zone | N | — |
| Acrylic insert 10 mm | N | — |
| Applied letters relation | Via product composition, not Step 2 zone | Parallel bindings only |

---

## Runtime

| Scenario | Runnable without code change? | Note |
|----------|-------------------------------|------|
| A Simple ACP | Y (letters + support) | Scope none keeps ACP |
| B Routed + plexi | N as V6 composition | LIGHT-ROUTED QuoteWizard only |
| C Insert 10 mm | N as ACP zone | Layer flag only |
| D Letters top + routed bottom | **N** | First fail at binding/FinishSetup |

BE `:8001` reported **STALE** — runtime persistence for recent fixing field guarded; does not change mixed-face structural finding.

---

## Dead / conflict pieces (do not clean in this GO)

- `TPL-BOND-CASETAT` legacy string
- Unbound `DECORATIVE_VECTOR`
- Dual illuminated vs boxed product authorities
- `plexiInserts10mm` as nesting hint ≠ insert treatment
- Dossier `task_rules` as fake task SoT if misread
