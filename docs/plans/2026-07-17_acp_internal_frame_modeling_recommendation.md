# Recommendation — ACP Internal Frame Modeling

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Audit | `docs/audits/2026-07-17_acp_internal_frame_existing_contract_audit.md` |
| Source map | `docs/architecture/ACP_INTERNAL_FRAME_SOURCE_MAP.md` |
| Verdict | `INTERNAL_FRAME_EXISTS_AS_PARTIAL_CONFIGURATION` |
| **Decision recommendation** | **Option 2 — GO ACP LOCAL FRAME CONFIGURATION COMPLETION** |

---

## Problem (owner)

Panou ACP casetat needs an interior rigidization frame (steel or aluminium). Before creating a separate Component Template, establish whether the concept is already modeled. Audit shows: **partial boolean + clearance only**.

---

## Options evaluated

| Option | Meaning | Fit now? |
|--------|---------|----------|
| 1 | GO ACP INTERNAL FRAME COMPONENT TEMPLATE | Premature — no local nested model, processes, or reuse proof |
| **2** | **GO ACP LOCAL FRAME CONFIGURATION COMPLETION** | **Best** — extend existing ACP authority |
| 3 | FIX INTERNAL FRAME AUTHORITY CONFLICT | Not primary — single path exists; semantic drift on clearance label is a fixable sub-issue inside Option 2 |
| 4 | STOP FOR MATERIAL/PROFILE OWNER DECISION | Needed as **gates inside** Option 2, not as a full stop of modeling direction |

---

## Recommended direction (single)

**Keep the internal frame as local nested configuration of `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`.**

Do **not** create `Template cadru otel` / `Template cadru aluminiu`. Prefer:

```text
Cadru interior (nested on ACP)
  enabled: boolean
  material_option: steel | aluminium   # Resource Option
  profile: <canonical profile codes>     # owner-confirmed registry
  section / thickness / crossbars / setback  # dimensional rules TBD by owner
```

### Target flow (future build — not this audit)

```text
Step 1: marker checkbox only (keep)
Step 2: full frame config when enabled
PD: nested under ACP svg/mounting instance
Aggregate: local material + process projection when enabled; zero when off
Lifecycle: readiness via ACP (require nested completeness if enabled)
CPP: guarded until Resource Options + rates exist
```

---

## Why not Component Template now

- Frame is always part of the cased ACP assembly when used.
- No independent lifecycle or SVG binding today.
- Aggregate already treats ACP as one optional linked child; a second Component Template would risk authority confusion with Metal Premount — keep frame nested on ACP. Premount and internal frame remain **independent** concepts (no global XOR).
- Material should be Resource Option, not template fork.

Revisit Component Template only if a later product needs the same frame **without** ACP casing.

---

## Owner gates to confirm before implementation

| Gate | Recommendation |
|------|----------------|
| Model | config locală |
| Material | Resource Option (otel \| aluminiu) |
| Activare | checkbox marker (Step 1) |
| Step 2 | configuratie completa when enabled |
| PD | nested config |
| Aggregate | local projection |
| Lifecycle | prin ACP |
| CPP | guarded |
| Profile catalog | **owner must confirm** canonical sections (do not invent `20x20x1.5` as ACP default) |
| Clearance semantics | clarify whether `frame_clearance_mm` remains setback vs rename/split from reinforcement |

---

## Explicit non-goals (until GO implementation)

- No new Component Template
- No Product System seed of frame child
- No CPP pricing activation
- No Metal Premount reuse
- No schema/migration until nested contract is approved

---

## Implementation status (2026-07-18)

Owner GO `GO_ACP_INTERNAL_FRAME_LOCAL_CONFIGURATION_COMPLETION` started, then **STOPped**:

- Verdict: `FRAME_RESOURCE_OPTIONS_MISSING`
- Co-blocker: `FRAME_PROFILE_CATALOG_MISSING`
- No app implementation; no seed/migration; no free-text workaround.

## Next safe step

**Option 2 — STOP FOR FRAME PROFILE AND CROSSBAR OWNER RULES**

After owner confirms material Resource Option codes + profile catalog authority + crossbar policy, reopen local configuration completion.

Suggested first implementation slice (after catalogs exist):

1. Freeze semantics: `internal_frame_enabled` = reinforcement required.
2. Make clearance visible/editable (no hidden 5 mm).
3. Add nested Step 2 fields: material option + profile from catalog.
4. Project nested object into PD; Aggregate zero-when-off / quantity-guarded.
5. Lifecycle rule: enabled ⇒ nested required; else NOT_APPLICABLE.
6. Do **not** implement global XOR vs premount.

STOP — awaiting owner catalog decisions.
