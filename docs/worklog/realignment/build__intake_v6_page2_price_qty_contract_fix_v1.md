# Build: Intake V6 Pas 2 — qty plexiglas/forex + linii contract

**Date:** 2026-07-24  
**Status:** implemented (backend + live-list surfacing)

## Operator findings (Remus litere+ACM)

| Simptom | Cauză | Fix |
|---------|-------|-----|
| Plexiglas **4.5 m²** (față litere ~0.33) | Nesting VL aloca foaia întreagă / includea `support_panel` ACM | Exclude ACM din sheet VL + cap prorated fallback la geometria litere |
| Forex material **4.5 m²** | Același fallback ca plexi | Același |
| Debitare CNC Forex **7.42 ml** | Corect (perimetru) — CPP `debitare_spate` rămâne pod m² DEV | Neschimbat rate-urile (owner GO); UI CNC rămâne ml |
| Linii `letters_acm_conn_*` / `acm_*` „nu apar” | Există în dry-run, absente din logical list | Surfaced în lista Pas 2 |

## Verification

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_nesting_material_precision.py tests/test_gradi_logical_list_read_model.py -q
```

Hard-refresh Pas 2 Remus → Detalii linii: plexiglas ≈ față litere (nu 4.5), + bloc contract ACM/conn.
