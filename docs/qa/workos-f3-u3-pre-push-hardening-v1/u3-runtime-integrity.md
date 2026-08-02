# U3 runtime integrity

## Prior mismatch root cause

Wave 3 Vite (`:3036`) talked to a backend without matching `ALLOWED_ORIGINS` / process identity. Browser CORS blocked `/api/v1/system/local-compatibility`, so the local-compat guard showed **Backend local indisponibil** and blocked truthful page proof.

Not a Wave 3 redesign defect.

## Corrected runtime (this hardening)

| Item | Value |
|---|---|
| Sources | Controller HEAD (integrated F3+U3) |
| Backend | `127.0.0.1:8016` |
| Frontend | `127.0.0.1:3038` |
| DB | `backend/qa-dbs/u3-pre-push-hardening.db` (copy of `dev.db`; canonical untouched) |
| `WORKOS_GIT_COMMIT` | matches controller short SHA |
| CORS | includes `http://127.0.0.1:3038` |
| Auth | Dev Mode `VITE_ENABLE_DEV_AUTH=true` |

## Pages captured (day + dark)

| Page | URL |
|---|---|
| Product System | `/product-system/products` |
| Product Template detail | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` |
| Prețuri template | same + `?ps_legacy=1` → Admin/diagnostic → pricing tab |
| Pricing Registry | `/inventory/pricing` |
| Utilaje | `/utilaje` |
| Settings | `/settings` |
| Governance | `/governance` |

Capture results: `u3-capture-results.json` — 14/14 expectOk, zero integrity/CORS blocks.

## Ownership checks observed

- Continuity strip: Produs → Șabloane → Prețuri → Utilaje → Setări
- Template strip: „șablonul nu deține ratele de catalog”
- Utilaje framed as capacity/feasibility, not client tariff
- `rate_per_hour` not presented as client selling price on these admin surfaces

## Console

Pre-existing React Router v7 future-flag warning and nested `<button>` DOM nesting on Product System structure cards. No new duplicate-key warnings. No local-compat errors after CORS fix.
