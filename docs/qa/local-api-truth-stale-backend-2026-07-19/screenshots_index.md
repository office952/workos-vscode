# Local API truth — UI screenshots

| File | Config | Expected |
|------|--------|----------|
| `01_incompatible_stale_8001.png` | `VITE_API_BASE_URL=http://127.0.0.1:8001` | Banner: Backend local incompatibil |
| `02_unavailable_59999.png` | `VITE_API_BASE_URL=http://127.0.0.1:59999` | Banner: Backend local indisponibil |
| `03_compatible_8002.png` | `VITE_API_BASE_URL=http://127.0.0.1:8002` | No compat banner |
| `04_intake_v6_compatible.png` | same + Intake V6 operator route | No compat banner; Intake loads |

All captures from live Vite React app on `http://127.0.0.1:3000`.
