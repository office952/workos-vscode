# Build — ACM panel-alone Intake offer path v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Fixture** | `docs/worklog/realignment/audit_assets/remus_acm_letters_svg_v1/doar-panou.svg` (~200×50 cm) |
| **Boundary** | Intake composition + authority + VL capture bypass for ACM-only; no Letters composition; no shell_finish→CostEngine; Form System ACM-root spine deferred |

## Owner intent

Offer **Panou Alucobond casetat** alone (`applied_content=none`) before Letters↔ACM composition.

## Delivered

1. **Composition** `support_only` (was `support_only_pending`) — recommendable + confirmable ACM-only product  
2. **UI label** — „Panou Alucobond casetat”  
3. **Authority** — single-panel segmentation = N/A (not `offer_ferm_unavailable`)  
4. **Confirm** — persists `applied_content=none` on finish / payload / quote_input  
5. **Runtime capture** — suppresses VL letter/artwork fatals for support_only under VL Intake root  

## Operator path (Remus)

1. Intake V6 → upload `doar-panou.svg`  
2. Confirm layer `Alucobond Casetat` = `support_panel`  
3. Instantiere AcmPanel → geometry ~2000×500 mm  
4. Confirm construcție (3 mm, L1/L2) + composition „Panou Alucobond casetat”  
5. Dry-run / provisional ACM lines → firm eligibility when technical+composition confirmed  

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_product_composition_recommendation.py tests/test_acm_commercial_geometry_v1.py tests/test_intake_v6_acm_panel_only_capture_filter.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx
```

## Deferred

- Form System backbone ACM as `ROOT` (today only VL is owner-valid for capture map)  
- QuoteWizard ACM field set  
- shell_finish → CPP foil lines  
- Letters composition / Composer persist  
