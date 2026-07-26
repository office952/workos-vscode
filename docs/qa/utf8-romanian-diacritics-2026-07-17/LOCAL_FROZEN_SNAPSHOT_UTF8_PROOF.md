label: LOCAL FROZEN SNAPSHOT UTF8 PROOF
backend: http://127.0.0.1:8001
frontend: http://127.0.0.1:3000
routes:
  - GET /api/v1/product-system/quote-snapshot-v2/QSN2-2026-0002 -> 200, Față present, mojibake absent, commercial_total 3549.1286
  - GET /api/v1/entities/orders/92402 -> 200, total_amount 3549.1286, mojibake absent
  - GET /api/v1/entities/quotes/3 -> 200, mojibake absent
  - GET /api/v1/execution/plan/92402 -> 200, Romanian task labels clean
ui:
  - http://127.0.0.1:3000/execution/92402 -> Pregătire/Tăiere CNC față/Manoperă/Șablon clean; no mojibake
  - order total unchanged 3549.1286 / 3.549,13 RON
