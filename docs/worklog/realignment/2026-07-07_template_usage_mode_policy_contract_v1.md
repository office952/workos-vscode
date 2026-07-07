## TASK

TEMPLATE_USAGE_MODE_POLICY_CONTRACT_V1

## HEAD before work

- `201fb0e`

## Safety state

- `git status -sb`: no staged files; tracked worktree clean
- `git diff --cached --name-only`: empty
- `git status --short --untracked-files=no`: empty

## Current policy map

- Root offerable today:
  - `TPL-VOLUMETRIC-LETTERS_v2`
- Candidate product, not root offerable:
  - `TPL-VOLUMETRIC-LOGO_v1`
  - `TPL-ACM-CASSETTED-PANEL` documented as future candidate only
- Component-only internal modules:
  - `TPL-METAL-PREMOUNT-STRUCTURE_v1`
  - `TPL-VOLUM-ALUMINIU_v1`
  - face/back/led/finish logo and letters subtemplates

## Files changed

- [backend/services/template_usage_mode_policy.py](c:/Users/offic/workos_app_vs/backend/services/template_usage_mode_policy.py)
- [backend/services/active_template_scope.py](c:/Users/offic/workos_app_vs/backend/services/active_template_scope.py)
- [backend/tests/test_template_usage_mode_policy.py](c:/Users/offic/workos_app_vs/backend/tests/test_template_usage_mode_policy.py)
- [backend/tests/test_active_template_scope.py](c:/Users/offic/workos_app_vs/backend/tests/test_active_template_scope.py)
- [frontend/src/lib/activeTemplateScope.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/activeTemplateScope.ts)
- [frontend/src/lib/activeTemplateScope.test.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/activeTemplateScope.test.ts)
- [docs/worklog/realignment/2026-07-07_template_usage_mode_policy_contract_v1.md](c:/Users/offic/workos_app_vs/docs/worklog/realignment/2026-07-07_template_usage_mode_policy_contract_v1.md)

## Tests run

- backend focused availability/scope/policy tests
- frontend focused activeTemplateScope test
- `git diff --check`

## Explicit confirmation

- No Logo root activation
- No ACP root activation
- No Pricing changes
- No Quote/Order changes
- No Execution changes
- No DB / seed / migration work

## Next recommended slice

- `VECTOR_LOGO_TO_LINKED_CHILD_COMPOSITION_GUARD_V1`