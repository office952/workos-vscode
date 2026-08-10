# SETTINGS_RUNTIME_EVIDENCE

**GO:** WORKOS_SETTINGS_AUTHORITY_AND_PERSISTENCE_AUDIT_V1  
**HEAD:** `bd7c61fd`  
**DEMO_DB_ONLY:** YES  
**OWNER_DEV_DB_WRITES:** 0  
**API base:** `http://127.0.0.1:8000`  
**UI:** `http://127.0.0.1:3000/settings`  
**DB (uvicorn log):** `C:/w/psiso/backend/demo/workos_demo.db`

---

## 1. Health / DB

- `GET /health` → 200 `{"status":"healthy"}`
- Startup log confirms demo DB path (not `backend/dev.db`)

---

## 2. Company commercial write probes (demo only)

Script: `probes/run_settings_authority_probes_v1.py`  
Results: `probes/probe_results.json`

| Step | Result |
|------|--------|
| GET before | `default_vat_pct=21`, `eur_to_ron_rate=5` |
| PUT VAT 19 | 200; GET confirms 19 |
| PUT FX 4.9876 | 200; GET confirms 4.9876 |
| Restore originals | 200; GET `21` / `5` |
| Verdict | `vat_persist_roundtrip=PASS`, `fx_persist_roundtrip=PASS`, `restore_originals=PASS` |

---

## 3. Cost engine / recurring (read)

| Endpoint | Status | Summary |
|----------|--------|---------|
| `GET /api/v1/cost-engine/config` | 200 | EUR; overhead profile default; `cost_ora_manopera_default=null` |
| `GET /api/v1/cost-engine/base-config` | 200 | valid; hours 1176; avg labour 43.7925 EUR; overhead 0 |
| `GET /api/v1/entities/recurring-payments` | 200 | total 0 |

---

## 4. SmartBill (READ/HEALTH ONLY)

Correct paths:

- `GET /api/v1/integrations/providers/smartbill/config` → 200  
  `enabled=false`, `token_present=false`, `username_present=false`, `source=app_settings`  
  **No secret/token values captured.**
- `GET /api/v1/integrations/providers/smartbill/health` → 200  
  `status=disabled`, missing SMARTBILL_* fields listed as names only.

Wrong paths in first probe draft (`/api/v1/integrations/smartbill/...`) → 404; corrected in same results file.

**No** test-connection, **no** config PUT, **no** token clear, **no** external side-effect calls.

---

## 5. UI screenshots

| File | Tab |
|------|-----|
| `screenshots/01-societate.png` | Societate — live VAT 21 / FX 5 + static SignTech mock + static banner |
| `screenshots/02-plati-repetitive.png` | Plăți — empty; KPIs 0; no FX conversion note |
| `screenshots/03-cost-intern.png` | Cost Intern — base-config loaded; honesty badges |
| `screenshots/04-integrari.png` | SmartBill disabled / credentials absent |

---

## 6. Static identity evidence (UI)

Observed on Societate: SignTech Advertising SRL, RO12345678, Banca Transilvania, etc. — matches `mockData.companySettings` literals. Banner warns static.
