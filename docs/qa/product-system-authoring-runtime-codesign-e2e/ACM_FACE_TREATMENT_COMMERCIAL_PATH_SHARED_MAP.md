# ACM / Bond Face-Treatment Commercial Path — Shared Map

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| CP0 | `ACM_FACE_TREATMENT_COMMERCIAL_PATH_CP0_FREEZE.md` |
| Allowlist | `ACM_FACE_TREATMENT_COMMERCIAL_PATH_ALLOWLIST.md` |

## Agents A–G

| Agent | Scope |
|-------|--------|
| A Identities / registry | Reconfirm routed + insert codes; relief badge; legacy dead |
| B Domain / PT | `acm_face_treatments_v1` normalize + confirm coexistence |
| C PD / Aggregate | Project instances; no double ACM sheet |
| D Quantity / ops | Treatment qty keys + guarded process intents |
| E CPP / EIC | Honest optical BLOCK; panel CPP isolation |
| F UI / Readiness | Distinct face-treatment section; scoped readiness |
| G QA / Evidence | Tests, screenshots, runtime JSON, final report §§1–42 |

## Dual-axis map

```text
TPL-ACM-BOXED-MOUNTING-SUPPORT_v1
├── Axis A (unchanged this build)
│   ├── applied_content XOR letters | logo
│   └── metal_frame optional (acp_internal_frame)
└── Axis B (this build)
    └── acm_face_treatments_v1
        ├── routed_cutouts[]  → FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT
        │                      → ACP-LOCAL-MODULE-ROUTED-BACKLIT
        └── acrylic_inserts[] → FACE-TREATMENT-ACRYLIC-INSERT (~10 mm variant)
                               → ACP-LOCAL-MODULE-ACRYLIC-INSERT
                               → UI badge RELIEF_PLEXI_10MM (optional display)
```

## Commercial spine

```text
typed PT config (finish_setup.acm_face_treatments)
  → ConfirmJobProductTruth pin (acm_face_treatments bag)
  → PD canonical_values.acm_face_treatments + local module instances
  → Aggregate projection (identity/ops intents; no panel sheet fold-in)
  → Quantity matrix (treatment keys ≠ PANEL_QUANTITY_KEYS)
  → CPP/EIC (panel OK; optical treatment lines BLOCKED honestly)
  → Readiness (optional treatments absent → not panel blocker)
  → UI "Tratarea feței Bond/ACM"
```
