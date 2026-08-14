# Lane G — legacy / dead (Wave 4)

Ugly ≠ dead. Consumer evidence required.

| Artifact | Class |
|----------|--------|
| `TPL-VOLUMETRIC-LETTERS_v2` | ACTIVE_REQUIRED |
| `TPL-VOLUMETRIC-LETTERS` (alias) | ACTIVE_COMPAT |
| `TPL-VOLUMETRIC-LETTERS_v1` | ARCHIVED |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | ACTIVE_REQUIRED |
| `TPL-ACM-CASSETTED-PANEL` | FUTURE |
| `TPL-ACP-LIGHT-ROUTED` | ARCHIVED |
| `TPL-BOND-CASETAT` | LEGACY_REFERENCED (alias → boxed) |
| `TPL-VOLUMETRIC-FACE/BACK/LED/FINISH` + `TPL-VOLUM-ALUMINIU_v1` | LEGACY_REFERENCED (used by letters root) |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | LEGACY_REFERENCED (BE root_offerable; FE scope omits) |
| `TPL-VOLUMETRIC-LOGO_v1` + children | FUTURE / LEGACY_REFERENCED (root blocked) |
| `TPL-COMP-LETTER-*` / `TPL-LETTERS-COMPOSER_v1` | FUTURE |
| `volumetric_*` services | ACTIVE_REQUIRED |
| Work Intake V2 `/intake-v2` | LEGACY_UNUSED (removed from `frontend/src`) |
| `/demo/*` | REMOVE_CANDIDATE_ONLY (dev) |

**LEGACY_REMOVE_CANDIDATE_COUNT = 0** for production templates (demos only).
