# GRADI-CURAT UI PRODUCT CONFIGURATION + PRODUCT DEFINITION RESUME — REPORT

## 1. Verdict

GRADI_CURAT_UI_FIRST_BLOCKER_FOUND

## 2. Repository truth

- Branch: `feature/product-system-active-path-isolation-v1`
- Starting HEAD: `b3eb437`
- Docs-only follow-up commit for this walkthrough (see §24)

## 3. Runtime truth

- Frontend `:3000`, backend `:8001` — not restarted
- Same workspace reused

## 4. Exact UI route

`http://127.0.0.1:3000/intake-v6/11891d68-c4c8-4719-acc5-f8fcb22a44af/operator`

## 5. Workspace/file identity

- workspace_id: `11891d68-c4c8-4719-acc5-f8fcb22a44af`
- visible: `IV6-5A24B7B0`
- file: `gradi-curat.svg`
- hash match: YES (`593C4D43…AB6CF1`)

## 6. Analyzer result visible in UI

YES — dimensions ~5087×600 mm; 6 layers; thumbnail/preview controls present.

## 7. Composition visible in UI

YES — Litere volumetrice + logo volumetric · Confirmata · 2 segmente linked.

## 8. Initial visible blocker

`finish_setup_incomplete` / Acțiune necesară înainte de Confirmare (before owner config).

## 9. Owner answers G1–G6

- G1 FRONT_LIT
- G2 Plexiglas opal 3 mm, alb mat, vinyl NO
- G3 Al 0.6 mm, 60 mm, alb
- G4 PRINTED_AND_LAMINATED + laminare mată; apply after assembly
- G5 INSTALLATION_TEMPLATE; installation YES; no continuous Forex/ACM plate
- G6 COOL_WHITE

## 10. UI actions performed

See worklog table. Key writes: Cool white; mounting prep+site; no Continuă-to-Confirmare success claim. Auto-sync persisted draft finish_setup including forced Forex.

## 11. Persisted finish setup

Present with `confirmed=true` via UI auto-sync. Includes cool/illuminated/mounting as intended; **backing_mode remains `forex_10_no_bevel`** against owner rule.

## 12. ProductDefinition result

Preview OK with workspace context; not quote-ready (`runtime_capture_blocked`).

## 13. Active/inactive modules

geometry_svg active; other modules follow incomplete/forced backing truth — not accepted as owner-complete.

## 14. Materials/processes

Live estimate still lists Forex 10 mm continuous plate — contradicts G5.

## 15. Readiness and missing fields

- readiness: `runtime_capture_blocked`
- adapter: `MOUNTING_SOLUTION_MISSING`
- owner gap: no UI control for letter-back `none`

## 16. Last successful handoff

Partial UI mapping of G1/G3/G4(approx)/G5(mount)/G6; analyzer/composition already PASS.

## 17. First next blocker

Cannot express **no continuous Forex letter backing** in Intake V6 UI (`INTAKE_V6_BACKING_MODE_OPTIONS` Forex-only; tests assert “Fără spate” absent).

## 18. Root-cause classification

INTAKE_UI

## 19. UI evidence

`docs/qa/gradi-curat-e2e/ui-walkthrough/` — owner answers, before/after JSON, post_owner_ui_state.json. Screenshots via browser session (customer artwork not committed).

## 20. Runtime writes

UI auto-sync finish_setup on workspace `11891d68-…` only. No quote/order/execution/inventory.

## 21. Forbidden paths confirmation

- browser UI used: YES
- no API-only substitute for primary proof: YES
- same workspace/SVG: YES
- no new workspace/quote/order/DB/code/migration/seed/SVG edit: YES
- did **not** API-inject `backing_mode=none`: YES

## 22. Recommended next action

correct one coherent Intake UI/contract blocker

## 23. Files changed

Docs/evidence + worklog only.

## 24. Commit

Docs/evidence only: YES  
Hash: *(after commit)*

## 25. Push/PR

NO / NO

## 26. Exact owner verification

- URL above · Configurare · tabs Finisaje/Iluminare/Montaj
- Expected after fix: Finisaj spate option “Fără spate / none”; no Forex plate in materials; Cool white; șablon + site install; ACM off
- Click path: Configurare → set finishes/LED/montaj → Continuă Confirmare → PD ready without Forex plate

## 27. Honest opinion

Owner config mostly maps, but the product system still forces a Forex letter back that the owner explicitly refused. Stopping here is correct fail-closed behavior for truth — not a PD math failure.

## 28. Roadmap awareness checkpoint

- Score: 7/10
- Position: same-scenario E2E; finish_setup was the right surface
- Dead pieces: no legacy `/price`, no stitch
- Forbidden scope held
- Cat sunt in directia stabilita: **72/100%**
