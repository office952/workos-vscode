## Premount + ACM capability truth check (Phase 4)

### Canonical templates in scope

- `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`
- `TPL-METAL-PREMOUNT-STRUCTURE_v1`

### Owner truth (from task contract)

For both ACM boxed mounting support and Metal premount structure:
- `root_offerable = true`
- `linked_child_offerable = true`
- `internal_only = false`

### Source of capability policy (as-is)

Backend capability derivation:
- `backend/services/product_system_template_readiness_service.py` → `_derive_capabilities(...)`
  - uses `services/template_usage_mode_policy.get_template_usage_mode_policy(...)`
  - sets `internal_only` when `policy.component_only` or candidate-only without root offerable, or internal roles.

Template usage mode policy (as-is):
- `backend/services/template_usage_mode_policy.py`

### Findings (mismatch proof)

#### ACM boxed mounting support

Explicit policy exists:

```88:97:backend/services/template_usage_mode_policy.py
TPL_ACM_BOXED_MOUNTING_SUPPORT_V1: TemplateUsageModePolicy(
  template_code=TPL_ACM_BOXED_MOUNTING_SUPPORT_V1,
  root_offerable=True,
  linked_child_allowed=True,
  candidate_only=False,
  component_only=False,
  owner_go_required=False,
  reason="Owner-approved offerable boxed ACM mounting support; standalone PS + Intake linked child.",
),
```

This matches owner truth.

#### Metal premount structure

No explicit policy exists; it is included in `_LETTER_MODULE_CODES` and defaulted to a **component-only** policy:

```25:33:backend/services/template_usage_mode_policy.py
_LETTER_MODULE_CODES = (
  TPL_METAL_PREMOUNT_STRUCTURE_V1,
  ...
)
...
for code in _LETTER_MODULE_CODES:
  _RAW_POLICIES.setdefault(code, _component_policy(... component_only=True ...))
```

Therefore, current policy treats premount as:
- `root_offerable = false`
- `linked_child_allowed = true`
- `component_only = true`
→ which implies readiness `internal_only = true` in `_derive_capabilities(...)`.

This **violates** owner truth.

### Decision

- This mismatch is **policy code**, not DB seed/migration.
- Per task constraint: we **will correct code-policy** when no migration is required.

### Planned correction (next step)

Add an explicit `TemplateUsageModePolicy` entry for `TPL-METAL-PREMOUNT-STRUCTURE_v1` matching owner truth:
- `root_offerable=True`
- `linked_child_allowed=True`
- `component_only=False`
- `candidate_only=False`
- `owner_go_required=False`

