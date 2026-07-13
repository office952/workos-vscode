## Test matrix — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

### Backend (pytest) — required

Identity boundary:
- Canonical formatting normalization accepted (trim/case)
- Known legacy alias returns explicit resolution metadata
- Active compilation identity gate rejects legacy alias
- Canonical codes accepted for:
  - `TPL-VOLUMETRIC-LETTERS_v2`
  - `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`
  - `TPL-METAL-PREMOUNT-STRUCTURE_v1`

Route enforcement (identity rejection):
- `/api/v1/product-system/aggregate/{template_code}` rejects `TPL-VOLUMETRIC-LETTERS`
- `/api/v1/product-system/product-definition/{template_code}` rejects alias
- `/api/v1/product-system/cost-bom-preview/{template_code}` rejects alias
- `/api/v1/product-system/quote-snapshot-v2/(preview|freeze)/{template_code}` rejects alias

Capability truth:
- Premount + ACM policy is root+linked-child offerable, not internal-only
  - Verified via policy file change (see `premount-acm-capability-truth.md`)

Implemented tests:
- `backend/tests/test_template_architecture_scope.py` (updated)
- `backend/tests/test_product_system_identity_boundary.py` (new)

Command used:

```bash
cd backend
<existing-venv-python> -m pytest tests/test_template_architecture_scope.py tests/test_product_system_identity_boundary.py -q
```

### Frontend — required (minimal)

This slice intentionally avoids Product Detail and catalog redesign.\n\nFrontend coverage will be provided via runtime verification + screenshots (see `runtime-verification.md`) and existing Product System E2E smoke where applicable.

