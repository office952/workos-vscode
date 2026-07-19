# INTAKE V6 SUPPORT ROLE TRUTH REPAIR REPORT

## 1. Verdict

**PASS** — first-paint ACM support proposal, Contur suport persistence, server/client Page 1 hydration bridge, and Confirmare access gate repaired inside the GO boundary.

## 2. Mini decizia agentului

Repair proposal + persistence + hydration; do not resume Design System expansion until owner GO.

## 3. Git state

Branch `feature/product-system-active-path-isolation-v1`. Foreign WIP left untouched.

## 4. Baseline and audit commit

| Item | Hash |
|------|------|
| Audit docs-only | `4dede53d8fd220d0773da318f6e7384bdd532048` |
| Message | `docs(intake-v6): audit layer role and template wiring` |
| Visual pilot | `f39c260` |

Audit commit includes QA pack + worklog (verified via `git show --name-only`).

## 5. Runtime environment

FE `http://127.0.0.1:3000` with `BACKEND_PORT=8003` · BE `http://127.0.0.1:8003` healthy.  
Note: default Vite proxy targets `:8001`; acceptance required explicit `BACKEND_PORT=8003`.

## 6. Root cause

`pseudo:* → face` short-circuit; FinishSetup race before analysis persist + incomplete-role binding sync; server upload without `svg_source_text`; Confirmare gated like Review.

## 7. Repair checkpoint

`REPAIR_CHECKPOINT.md` written before implementation.

## 8. Proposal algorithm before

All `pseudo:*` → `face` / high.

## 9. Proposal algorithm after

Soft candidates → metrics (multi-shape face) → geometry refine (outer/low-complexity + letter sibling → `support_panel`).

## 10. Geometry evidence used

Sibling closed/subpath complexity, filled/bbox area dominance, outer closed-contour width/height match. **Not color.**

## 11. Ambiguity behavior

Ambiguous equal support-shaped fills without outer winner → `unknown`.

## 12. Operator confirmation boundary

Proposals remain `pending` / `confirmedRole=null` until operator selects. No auto composition / segmented confirm.

## 13. FinishSetup persistence root cause

Early association needs persisted `layer_role_setup`; letter-binding FinishSetup ran while roles incomplete; Contur suport error copy wrapped all FinishSetup failures; segmented proposal could couple to support write.

## 14. FinishSetup persistence repair

Flush analysis-bundle with explicit confirmation → SUPPORT_CONTOUR write → segmented proposal secondary; skip incomplete-role binding sync; honest error messages.

## 15. Client ingest path

Unchanged canonical `analyzeSvgFileForIntakeV6Client` / `analyzeSvgString`.

## 16. Server ingest path

`upload_svg_to_intake_v6_workspace` now stores `svg_source_text` (clears stale `svg_analysis_json` on replace).

## 17. Hydration alignment

`intakeV6ServerUploadHydrationBridge` re-runs client analyzer when source text exists without nest2 report.

## 18. Confirmare access

`canAccessIntakeV6Step('confirm')` requires analysis ready **and** product composition confirmed. Review remains accessible.

## 19. Template/binding invariants

Preserved: face → `LETTER_VECTOR_SET` → `TPL-VOLUMETRIC-FACE_v1`; support + contour → `SUPPORT_CONTOUR` → `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`.

## 20. Inactive-zero verification

No Montaj/PD/Aggregate/segmented contract redesign. Unconfirmed support does not auto-confirm segmented.

## 21. Tests

Focused Vitest support/hydration/readiness PASS. Backend early support FinishSetup 6 passed. Pre-existing ana-maria stroke logo test fail untouched.

## 22. Live fixture matrix

| Fixture | Result |
|---------|--------|
| ACM segmented client | PASS — Contur suport proposal, binding, reload |
| Simple letters | PASS — face, no false support |
| Server upload | PASS — source text + Page 1 hydrated |

Evidence: `runtime/repair_live_summary.json`.

## 23. Screenshots

Under `screenshots/01_acm_client_initial.png` … `05_server_upload_hydrated.png`.

## 24. Honest operator assessment

Operator now sees Contur suport as the first proposal for the ACM panel; must still confirm roles. Confirmare stays locked until composition is confirmed in Review.

## 25. Hidden regressions

No color heuristics; no DS/Montaj/pricing/schema changes; foreign WIP untouched. Proxy misalignment (`:8001` vs `:8003`) is an ops risk — documented.

## 26. Files modified

See worklog. New: refine + hydration bridge + tests + QA pack.

## 27. Files intentionally not modified

PD/Aggregate, template registry, Montaj IA, pricing, Design System pilot chrome, migrations/seeds, segmented/electrical contracts.

## 28. Dead pieces check

No dead second analyzer. Soft face/support candidates remain for operator UI.

## 29. Worklog

`docs/worklog/realignment/2026-07-19_intake_v6_support_role_truth_repair.md`

## 30. Commit

`fix(intake-v6): repair support role proposal and persistence` (hash after commit).

## 31. Metoda de lucru si logica abordarii

Checkpoint → geometry evidence → persistence race → hydration bridge → Confirmare gate → focused tests → live fixtures with correct proxy → isolated commit.

## 32. Roadmap awareness checkpoint

Order preserved: proposal → confirm → binding → persistence → then premium UI.

## 33. Cat sunt in directia stabilita

Cat sunt in directia stabilita: 97/100%

## 34. Ce am construit este conform planului?

**DA** — Tracks A–D delivered inside GO; no forbidden redesigns.

## 35. Can visual DS work resume?

**DA, after owner GO** — wiring first-paint truth for ACM/support is repaired on mandatory fixtures; keep DS scoped to letter pilot, no global expansion.

## 36. Next recommended build

Owner-gated: resume letter Design System polish only (no Montaj/pricing/global DS), with fixture smoke that Contur suport proposal remains correct.
