# Owner Decision Sheet — Structural Resource Options

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Status | **PARTIAL OWNER_CONFIRMED** — registry model + materials + frame/crossbar rules; **profiles DEFERRED** |
| Related | `ACP_INTERNAL_FRAME_OWNER_RULES.md`, `STRUCTURAL_RESOURCE_OPTIONS_AUTHORITY.md` |

---

## Confirmed summary

| Item | Status | Value |
|------|--------|-------|
| Registry location | **OWNER_CONFIRMED** | **D** — shared technical catalog + pricing map (pricing later) |
| Pricing mapping | **OWNER_CONFIRMED** | Separate; missing price ≠ invalid technical resource |
| Storage MVP | **OWNER_CONFIRMED** | Versioned code/config; no DB/migration V1 |
| Materials | **OWNER_CONFIRMED** | `MAT-STRUCT-STEEL`, `MAT-STRUCT-ALUMINIUM` |
| Spelling | **OWNER_CONFIRMED** | `ALUMINIUM` (+ alias `aluminum`) |
| Profile naming | **OWNER_CONFIRMED** | `PROFILE-SHS/RHS-{W}X{H}X{T}`; no material in code |
| Shapes | **OWNER_CONFIRMED** | SHS + RHS |
| Initial profile list (ACP) | **DEFERRED** | Empty — `PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED` |
| Frame formula | **OWNER_CONFIRMED** | panel − 2×thickness − 2 mm; fold-independent |
| Fit allowance | **OWNER_CONFIRMED** | 2 mm total fixed |
| Clearance min/max | **NOT_APPLICABLE** | |
| Steel spacing | **OWNER_CONFIRMED** | 1000 mm |
| Aluminium spacing | **OWNER_CONFIRMED** | 750 mm |
| Crossbar mode | **OWNER_CONFIRMED** | Suggest + operator confirm + override reason |
| XOR frame↔premount | **OWNER_CONFIRMED** | No global XOR |

---

## Rejects (OWNER_CONFIRMED)

- ACP-scoped `OPT-ACP-FRAME-MAT-*`
- Premount/lightbox as ACP technical authority
- Free-text profiles
- Hidden 5 mm default as policy
- Seed/migration for V1 technical registry

---

## Next GO after this build

| Gate | Status |
|------|--------|
| Confirm ≥1 ACP profile section | **Required** before Step 2 complete / E2E green |
| Pricing mapping | Later — Option 1 after technical review |
| Quantity/BOM detail | Later — may stay GUARDED |

See: `docs/decisions/ACP_INTERNAL_FRAME_OWNER_RULES.md`
