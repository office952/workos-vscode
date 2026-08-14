# Wave 4 gap closure — role / theme coverage

Guard: `ShellPathGuard` → `pathAllowedForRole`. Denied → `getRoleHomePath`.

| ROLE | ROUTE | ROLE_ALLOWED | ROLE_PURPOSE | Theme duty |
|------|-------|--------------|--------------|------------|
| admin | `/product-system/*` | YES | catalog + workshops + planned + blueprint/output | Initial Wave 4 L+D on products/modules/gov; gap-closure L+D on workshops + remaining planned |
| admin | `/modules` `/governance` | YES | system map / gates | Initial Wave 4 L+D — not recaptured |
| manager | `/product-system/*` | YES | `view:products` — same V2 page as admin | Initial light; **gap-closure dark** |
| manager | `/modules` `/governance` | NO | no `view:modules` / `view:governance` | **NOT_APPLICABLE** — lands `/shop-floor` (initial denial shot) |
| sales | `/product-system/*` | YES | `view:products` | Initial light; **gap-closure dark** |
| sales | `/modules` `/governance` | NO | — | **NOT_APPLICABLE** — lands `/quotes` |
| operator | `/product-system/*` | NO | shop-floor only | **NOT_APPLICABLE** — lands `/shop-floor` |
| operator | `/modules` `/governance` | NO | — | **NOT_APPLICABLE** |
| sales/manager | blueprint / output-blocks | YES (same `view:products` prefix) | same pages as admin | **NOT_APPLICABLE** material difference — do not duplicate admin captures |

**ROLE_COVERAGE_RESOLVED = YES**  
**LIGHT_DARK_REACHABLE_SURFACES_COMPLETE = YES**  
**LIGHT_DARK_MISSING = 0** for required reachable pairs.

Do not assume every role needs every theme on every audit/dev page.
