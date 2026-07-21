# ACM Boxed Support Composition Extension — CP0 Freeze

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `5dfe807a` (reconfirmed) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Status | **FROZEN** — owner Decision **A** locked |
| Previous STOP | `BOND_SECOND_PRODUCT_CONFIGURATION_FINAL_REPORT.md` (closed by A) |
| Engine | native inline (no `.compound-engineering/config.local.yaml`) |

## Owner decision readback

| Item | Locked value |
|------|----------------|
| Option | **A** — extend existing ACM boxed; no new panel/composite root SKU |
| Root | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Product name (RO) | Panou Alucobond casetat cu conținut volumetric (compoziție) |
| Family | `panouri_acp_iluminate` / Panouri ACP / ACM |
| Version | composition extension `v1` on existing root |

## Frozen identities

| Freeze field | Frozen ID / rule |
|--------------|------------------|
| Bond / panel root | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Letters content pack | Reuse VL **component** PTs: `TPL-VOLUMETRIC-FACE_v1`, `TPL-VOLUMETRIC-BACK_v1`, `TPL-VOLUM-ALUMINIU_v1`, `TPL-VOLUMETRIC-LED_v1`, `TPL-VOLUMETRIC-FINISH_v1` — **not** VL root as child (avoids ACM↔VL cycle with existing VL→ACM link) |
| Letters root reference | `TPL-VOLUMETRIC-LETTERS_v2` remains first product / inverse path; no VL deep-dive, no publish, no formula copy |
| Logo content pack | Canonical logo **root** exists: `TPL-VOLUMETRIC-LOGO_v1` (+ children FACE/RETURN/BACK/LIGHTING/FINISH/MOUNTING). Branch kept **honestly blocked** for offerability (`candidate_only` / owner GO); composition edge may exist as draft intent |
| Logo forbidden substitute | Do **not** treat `TPL-VOLUMETRIC-LOGO-RETURN_v1` (or any return/cant) as full logo product |
| Metal frame | Domain `acp_internal_frame` on ACM mounting solution — **OPTIONAL**, operator-explicit; no automatic thresholds; **not** a PT; not `TPL-METAL-PREMOUNT-STRUCTURE_v1` |
| Applied content | XOR: `letters` **xor** `logo` (exactly one when content selected; none allowed for panel-only) |
| Trigger field (links) | `applied_content` with trigger values `"letters"` \| `"logo"` (no schema migration) |
| Req / opt / cond | Root shell required; content pack optional XOR; frame optional; mounting/finish/assembly remain root-owned |

## Shared composition map

```text
TPL-ACM-BOXED-MOUNTING-SUPPORT_v1   (root — panel identity/dims/material/casetare/finish/mounting/lifecycle)
├── applied_content = letters  → FACE, BACK, ALUMINIU, LED, FINISH   (reuse; separate_quote_line)
├── applied_content = logo     → TPL-VOLUMETRIC-LOGO_v1 pack        (draft/blocked offerability)
├── metal_frame                → acp_internal_frame domain (optional checkbox)
└── (existing) panel ops/materials / assembly
```

**Inverse of VL:** VL root may still optionally link ACM as child. Job-level exclusivity is operator intent (do not auto-merge both roots for one physical job).

## Non-scope (frozen)

No product publication; no VL publication; no auto-activate inactive children; no pricing redesign; no SVG/DWG/DXF; no ComponentTemplate/PI/CI tables; no Execution materialization; no new panel/composite SKU; dirty tree untouched outside allowlist.

## CP0 exit criteria

- [x] Owner Decision A accepted (no re-ask A/B/C)
- [x] Letters / logo / frame IDs frozen
- [x] XOR + optional frame rules frozen without schema migration
- [x] Allowlist + worklog section ready
- [ ] CP1–CP6 implementation (this run)
