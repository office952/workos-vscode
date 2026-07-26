# Build — Contract lines visible in Pas 2 list

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Workspace** | `7cedd889-eaf2-46f6-82c4-8ffe93958a56` |
| **Boundary** | CPP gate + logical-list display; no CostEngine rewrite |

## Live UI before

- Rail: **Detalii linii (20)**; falsely **Legături 6 linii** (those were `acm_*`)
- Sheet: 6× `commercial.acm_*` visible; **0× `letters_acm_conn_*`**
- API: dry-run `conn=0`, logical `17 VL + 6 ACM = 23`

## Root cause

1. `finish_setup.applied_content` empty/null after later writes
2. Dry-run CPP only received `quote_input` — **not** `product_composition_confirmed.applied_content=letters`
3. Gate `is_letters_acm_composition_active` stayed false → 7 connection lines never emitted
4. Rail labeled all `composition_contract_row_count` as „Legături”

## Fix

- Bridge confirmed `applied_content` into quote_input enrich (`intake_v6_priced_quote_dry_run_service`)
- `read_applied_content` prefers meaningful letters/logo over empty finish bags
- Split counts: `composition_acm_row_count` / `composition_connection_row_count`
- Rail: Legături = conn only; honest summary `VL + panou + legături`

## Live UI after

- **Detalii linii (27)** included (30 API − plexi merge − 2 diagnostic)
- Summary: `30 rânduri (VL 17 + panou 6 + legături 7 · țintă VL 21)`
- Rail: **Legături Litere↔Bond 7 linii**
- All 7 `letters_acm_conn_*` + 6 `acm_*` in sheet

## Count answer (this workspace)

| Bucket | Count |
|--------|------:|
| Dry-run commercial lines | **21** (8 VL-ish incl. ambalare/montaj + 6 ACM + 7 conn) |
| Logical list rows | **30** (17 VL core + 6 panou + 7 legături) |
| Operator included in Detalii | **27** |
| Earlier “20” | VL+ACM only, before conn emission |
| Earlier “23” | 17+6 ACM, before conn |

Neither 20 nor 23 was the full Remus composition set; full set is **17+6+7**.
