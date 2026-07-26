# GRADI-CURAT.SVG SAME-SCENARIO E2E DIAGNOSTIC — FINAL REPORT

## 1. Verdict

GRADI_CURAT_E2E_PARTIAL_FIRST_BLOCKER_FOUND

## 2. Repository truth

- Worktree: `C:\w\psiso`
- Branch: `feature/product-system-active-path-isolation-v1`
- Verified HEAD at start: `03c13bbef21f063414d0eda6bcffde2f691d6af6`
- Product-code commit present as ancestor: `0b97f7d` (not HEAD)
- Dirty unrelated worktree files existed; this task touched docs/evidence only

## 3. Runtime truth

- Backend `http://127.0.0.1:8001` healthy (`/docs` 200)
- Frontend `http://127.0.0.1:3000` healthy (200)
- Two LISTENING PIDs on `:8001` observed; no restart; no duplicate listener created
- Auth: `Bearer __DEV_BYPASS_TOKEN__`

## 4. Input file identity

| Field | Value |
|-------|-------|
| path | `C:\Users\offic\Desktop\fisiere-teste-svg\gradi-curat.svg` |
| size | 27173 bytes |
| SHA-256 | `593C4D439157B83CAB16C33D69CAF0AB426144D583FB1999FA7D1676D5AB6CF1` |
| modified | 2026-07-01T21:07:39.3136693+03:00 |
| original unchanged | YES |

## 5. SVG structure

- XML valid: YES
- Root: width `508.699cm`, height `60.003cm`, viewBox `0 0 519.77114 61.30898`
- Namespaces: SVG + xlink + Corel xodm
- Elements: 6 closed paths, 1 group, 0 text, 0 images, 0 use, 0 clip/mask
- Transforms: 0; style blocks: 0; duplicate IDs: 0; external refs: 0
- Stroke-only paths (est.): 2; fill paths (est.): 4
- Production-vector usable without modification: **likely YES** (vector paths; units declared in cm)

## 6. Geometry truth

| Quantity | Value | Class |
|----------|-------|-------|
| Physical width | 5086.99 mm | safely_derived (from cm) |
| Physical height | 600.03 mm | safely_derived (from cm) |
| viewBox | declared | directly_declared |
| Letter count | 19 | safely_derived (analyzer) |
| Letter perimeter | 21.1675 m | safely_derived |
| Letter face area | 1.2638 m² | safely_derived |
| Artwork area | 0.8005 m² | safely_derived |
| Cut contours | 28 | safely_derived |
| Inner holes | 8 | safely_derived |
| Logo vs letters | 4 face groups + 2 logos | safely_derived |
| Open paths | 0 | estimated from path `Z` |

## 7. Product interpretation

Letters + logo composition (“GRADI CURAT” style letter groups + two logo instances). Not ACM-mounted unless owner sells ACM.

## 8. Selected template

- Root: `TPL-VOLUMETRIC-LETTERS_v2`
- Linked composition: `TPL-VOLUMETRIC-LOGO_v1`
- Confirmed via analyzer recommendation + PUT composition confirmation

## 9. Required operator inputs

Must be provided before commercial-ready PD/quote:

- Illumination mode (yes/no → LED/PSU chain)
- Face/return finishes + return depth
- Backing mode confirmation
- Logo print/lamination truths
- Mounting scope (no silent ACM)
- Finish-target runtime capture

## 10. Handoff matrix

| step | input | identity | route/service | expected | actual | status | evidence |
|------|-------|----------|---------------|----------|--------|--------|----------|
| A | SVG file | ws `11891d68-…` | analyze + PUT analysis-bundle | persist analysis/geometry | 200; letter_count 19; composition recommended | PASS | `docs/qa/gradi-curat-e2e/` |
| B | analyzed workspace | same | GET pricing-input-preview | map geometry fields | width/height/letter_* mapped; not quote-ready | PASS | `pricing_input_preview.json` |
| B2 | composition recommendation | same | PUT product-composition-confirmation | confirm letters+logo | readiness `finish_setup_incomplete` | PASS | `composition_confirm_response.json` |
| C | intake without finish | same | PD preview + readiness | commercial-ready PD | modules pending; adapter blockers | BLOCKED | `first_blocker_evidence.json` |
| D–P | — | — | — | — | — | NOT_REACHED | — |

## 11. Last successful handoff

B2 — product composition confirmation (`letters_plus_logo`)

## 12. First blocking handoff

C — Intake V6 → commercial-ready ProductDefinition

## 13. Exact blocker

`finish_setup_incomplete` with adapter blockers for lighting plan, finish target, print/lamination unknowns, and mounting scope. PD preview exists but is not pricing/quote ready.

## 14. Root-cause classification

OWNER_DECISION

(Secondary: INTAKE_CONTRACT — required finish fields absent)

## 15. Evidence

`docs/qa/gradi-curat-e2e/` — static SVG JSON, analyzer summary, handoff matrix, pricing preview, PD preview, composition confirm, runtime state, cleanup log. Customer SVG text omitted from git artifacts.

## 16. Runtime writes performed

1. Create Intake V6 workspace  
2. Persist analysis-bundle  
3. Confirm product composition  

## 17. Cleanup result

No inventory/quote/order side effects. Workspace retained locally. SVG unchanged.

## 18. Forbidden paths confirmation

- legacy `/price` not used: YES  
- direct DB repair not used: YES  
- template injection not used: YES  
- mock data not used: YES  
- SVG not modified: YES  
- Product System not redesigned: YES  
- pricing not changed: YES  

## 19. Current continuous lineage

- intake/request: none created (workspace-only path)
- workspace: `11891d68-c4c8-4719-acc5-f8fcb22a44af`
- template: `TPL-VOLUMETRIC-LETTERS_v2` (+ confirmed logo composition item)
- quote snapshot / order / execution plan / task / session / stock / reconciliation: **none**

## 20. What remains unproven

Everything from commercial-ready ProductDefinition through ProductAggregate, 7G/7H, Quote/Order freeze, Execution Plan, materialization, reality, inventory actuals, post-job reconciliation, profitability coverage — for this same SVG scenario.

## 21. Recommended next action

owner product decision

## 22. Proposed correction boundary

- Product outcome: capture illuminated vs not, finishes, logo print/laminate, mounting for gradi-curat on workspace `11891d68-…`, then resume same-scenario path  
- Affected handoffs: C → E/F → G…  
- Likely systems: Intake V6 finish_setup / runtime capture / ProductDefinition modules / linked logo segment readiness  
- Forbidden scope: SVG edits, ACM silent add, legacy `/price`, DB repair, fixture stitching, pricing-rule invention  
- Migration necessary: NO  
- DB/runtime writes needed later: YES — only via real finish_setup + canonical quote/order APIs after owner decisions  

Do not implement in this task.

## 23. Files created/changed

- `docs/qa/gradi-curat-e2e/**` (evidence package)
- `docs/worklog/realignment/2026-07-16_gradi_curat_same_scenario_e2e_diagnostic.md`
- helper scripts under evidence dir (`_analyze_svg_static.py`, `_runtime_probe.py`)

## 24. Commit

Docs/evidence only: YES  
Hash: `dc14fbf6be2d1a291a0ae0c18a25546ffcd1a866`

## 25. Push/PR

NO / NO

## 26. Honest opinion

The real file travels cleanly through analyzer and Intake geometry mapping, and the letters+logo composition path is real — not a fake letters-only story. The first hard stop is exactly where WorkOS should stop: commercial truth that SVG cannot invent. That is a strong diagnostic result, not a failure of SVG ingestion.

## 27. Roadmap awareness checkpoint

- Score: 8/10  
- Current roadmap position: same-scenario Request→post-job proof; Stage A post-job accepted with limitations; this run starts Stage B on a real file  
- Dead pieces check: did not revive legacy `/price`, V3 catalog, or mock order 23099  
- Forbidden scope confirmation: held  
- Cat sunt in directia stabilita: **78/100%**
