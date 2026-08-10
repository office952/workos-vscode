# SETTINGS_PERSISTENCE_MATRIX

**Writes:** DEMO_DB_ONLY = YES · OWNER_DEV_DB_WRITES = 0  
**Live backend DB (proven log):** `C:/w/psiso/backend/demo/workos_demo.db`

| Control | Read path | Write path | Round-trip probe | Reload survives | After refresh | Classification |
|---------|-----------|------------|------------------|-----------------|---------------|----------------|
| TVA % | GET company-commercial-settings | PUT `{default_vat_pct}` | PASS (21→19→21) | YES | YES | PERSISTED |
| EUR/RON | GET same | PUT `{eur_to_ron_rate}` | PASS (5→4.9876→5) | YES | YES | PERSISTED |
| Company identity/bank/contact | FE mock only | none | N/A | N/A | always mock | NOT_PERSISTED / STATIC |
| Recurring payments | GET entities list | CRUD | Read OK (0 items); create **NOT_EXERCISED** this run | — | — | PERSISTED (API proven; empty demo) |
| Cost Intern config | GET config + base-config | PUT config | Read OK; edit save **NOT_EXERCISED** | — | — | PERSISTED (API live) |
| SmartBill config | GET config/health | PUT / test / clear | Read OK; writes **NOT_EXERCISED** | — | — | PERSISTED when saved (not probed) |
| Admin `/api/v1/settings` | 404 | — | — | — | — | ABSENT_ON_THIS_STACK |

Evidence file: `probes/probe_results.json`.

### Side-effect note (read path)

`CompanyCommercialSettingsService.get_or_create` / `get_settings` can **write** default `eur_to_ron_rate=5.0` when NULL. That is a persistence side-effect on read — separate from explicit Settings Save.
