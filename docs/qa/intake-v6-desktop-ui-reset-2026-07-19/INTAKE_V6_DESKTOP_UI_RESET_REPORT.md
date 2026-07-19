# INTAKE V6 DESKTOP UI RESET REPORT

## 1. Verdict

**PASS (audit / docs-only)** — every major desktop surface is inventoried, classified, and proposed for reset without implementation. Visual runtime is **not** accepted as finished UI; functional baseline `9f0efa0` remains frozen.

## 2. Mini decizia agentului

The desktop fails because alert chrome and nested ERP frames own L1 while product decisions (Față/Cant/Spate, lighting, ACP Fundal) sit below fold or in deep nests. Reset must rebuild presentation from operator goals — not polish existing cards. Truth stays; structure does not get a free pass.

## 3. Git state

| Item | Value |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD / baseline | `9f0efa0ce810ec0126ec6b3e1abe5d8d1e675602` |
| Foreign WIP | Present — untouched |
| This pack | Docs-only commit |

## 4. Runtime environment

| Surface | Record |
|---------|--------|
| FE | `http://127.0.0.1:3000` |
| Proxy | `BACKEND_PORT=8003` |
| BE | `http://127.0.0.1:8003` |
| Fixture | ACM segmented letters |
| Viewport | 1440×1000 (+ narrow 1100) |
| Fresh health | Read-only checks at audit start: FE/BE 200 |

## 5. Audit method

1. Live screenshots as visual truth.  
2. Component tree + testids from code ([explore map](261d53e3-d1cc-43d1-a3d7-279a25ac0200)).  
3. Domain truth: FinishSetup / composition / status spine frozen.  
4. Prior QA screenshots as secondary.  
5. Figma not used as runtime authority.  
6. No CSS/frontend/backend changes.

## 6. Operator goals

1. Recognize the physical product.  
2. Complete required decisions for the active surface.  
3. See system results without them dominating.  
4. Never miss real blockers.  
5. Ignore technical noise until needed.  
6. Always know the single next action (footer).

## 7. Full element inventory summary

See `DESKTOP_UI_ELEMENT_INVENTORY.md` (~80 indexed elements across shell, Page1, Finisaje, Iluminare, Montaj, Confirmare, pricing, footer). Marks include ORPHANED, DETACHED_HELPER, FALSE_URGENCY, NESTING_NOISE, UNEXPLAINED_DECISION.

## 8. Page 1 explanation

SVG + role cards are the real job. Composition confirm is a legitimate gate. Side-rail “use footer” is detached. Unmounted `IntakeV6SupportContourGeometryCard` is code orphan — runtime path is role select Contur suport (protected wiring). Technical metrics belong in disclosure.

## 9. Finisaje explanation

Letter anatomy pilot is the strongest product surface, but it loses the fold to Produs nesting + full-bleed rose banner + pricing. Helper “Finisaje pe layer…” floats. Nested letter cards are partly justified (zone ownership) but outer frames stack. Local Cant blockers are legitimate; global banner duplicates them.

## 10. Iluminare explanation

**Critical finding:** contract-generic fields (`Tip iluminare`, `PSU selectat`) float above `IntakeV6ReviewLightingSection`, with an engineering helper about “adapter iluminare specializat”. Operator sees two owners for one decision set, then empty vertical space, then specialized LED decisions/results. Results band is correct as L3; dual L2 is wrong.

## 11. Montaj explanation

Assembled from fragments: floating șablon contract fields, commercial accordion with empty inactive cards, Fundal/ACP deeply nested (solution → cyan box → grid → segmented/electrical), Product System badge + SVG hashes on L1, Avansat for leftovers. Cable/service-corner helpers appear out of condition. Product support should lead when ACM exists; commercial mounting is conditional.

## 12. Confirmare explanation

Page purpose (checklist + draft) is behind default-collapsed technical accordion — false calm. Status tile not alert-tier colored. Handoff receives blocker props but does not render them — inventory marks truth risk. Must first-paint blockers + checklist.

## 13. Warning and stress findings

≥6 alert-like surfaces often concurrent; “confirm composition” repeated ≥4×. See `WARNING_AND_STRESS_AUDIT.md`. Policy: one spine + local CTA + compact multi-issue chip.

## 14. Positive-confirmation findings

Autosave “Preturi si materiale actualizate”, file recognized, layer confirmed, composition confirmed — must never use rose/amber alert slabs. Header “Stare sistem” is FALSE_URGENCY relative to Intake task.

## 15. Orphaned text findings

See `ORPHANED_TEXT_AND_OWNERSHIP_AUDIT.md` (banner→footer hint, adapter helper, responsibility strings, inactive empty cards, Confirmare collapse).

## 16. Input ownership findings

| Input class | Owner | Importance proportional? |
|-------------|-------|--------------------------|
| Față/Cant/Spate | Letter/logo cards | Yes |
| LED/PSU | Should be one lighting group | Currently split — No |
| Mounting scope | Commercial cluster | Yes when relevant |
| Șablon area | Prep — conditional | Full-width often overweighted |
| ACP geometry | Fundal cluster | Yes but over-nested |
| Advanced screw/module | Avansat | Should stay weak |

## 17. Result ownership findings

LED results and pricing totals are correct as L3. Pricing currently also hosts product-gate warnings (wrong owner). Geometry mm readout is Result; hash is Technical.

## 18. Technical leakage findings

Product System badges, template IDs, SVG contour hashes, form-system responsibility strings, adapter engineering copy — all L1 leaks → L6 disclosure.

## 19. Nesting findings

Montaj Fundal reaches visual depth ~5; Produs ~4; Confirmare misuses technical accordion for primary content. Cap proposal: 3 frames page→input. See `NESTING_AND_LAYOUT_AUDIT.md`.

## 20. Desktop width findings

Grid bones (decision + rail) are sound; fold is wasted on alerts; short enums use full rows; wide monitors do not gain denser decision grids; footer dual-bar steals height.

## 21. Empty-space findings

Iluminare lower third empty; inactive Montaj site card empty but bordered; gaps between tabs and first decisions.

## 22. Pricing rail findings

Post-`9f0efa0` quieting is directionally correct (secondary, details on demand). Remaining issues: product-gate paragraph stress; missing-rate chip OK; must stay available, not dominate.

## 23. Footer/sticky/drawer findings

Footer is the correct next-action owner. Banner contradicts it (“next step in footer” while CTA is top). Drawer duplicates counts. Keep footer; demote banner; drawer for inventory only.

## 24. Current hierarchy failure

Alert bureaucracy and nested ERP chrome occupy attention; physical product decisions do not dominate the desktop viewport.

## 25. Proposed information hierarchy

L1 identity/task → L2 decisions → L3 results → L4 blockers only → L5 info/success → L6 technical. Documented in `DESKTOP_INFORMATION_HIERARCHY.md`.

## 26. Proposed desktop composition

Per-page region maps in `DESKTOP_COMPOSITION_PROPOSAL.md`. Independent agent proposal — not owner-predrawn.

## 27. What should remain visible

Product identity; required Confirm composition CTA when needed; active-tab primary decisions; commercial total/state; real blockers (compact); footer next action.

## 28. What should become contextual

Șablon/cable/site when scope/solution requires; service-corner only for ACP; segmented electrical when multi-panel; logo anatomy when logos exist.

## 29. What should move to technical disclosure

Template codes, hashes, Product System links, registry warnings, finish ownership notes, LED calc details, Avansat legacy, form-system responsibility strings.

## 30. What should be removed (presentation)

Banner “next step is in footer”; engineering adapter helper; empty bordered inactive cards; duplicate full-bleed status slabs; L1 Product System badges. **Not** remove truth/blockers.

## 31. What must remain functionally frozen

Support-role wiring, persistence, status count semantics, guidance spine, pricing math, analyzer, PD/Aggregate, Montaj IA/contracts, Confirmare honesty.

## 32. Implementation boundary

See `IMPLEMENTATION_BOUNDARY.md`. This pack: docs only.

## 33. Owner decision table

| # | Decision | Consequences | Recommendation | Confidence |
|---|----------|--------------|----------------|------------|
| D1 | Keep successful system confirmations persistently visible? | Persist → clutter; hide → less trust | Quiet ephemeral success (autosave toast/line), not persistent amber | High |
| D2 | Pricing during configuration: full rail vs compact summary only? | Full → commercial distraction; compact → may hide rates | Keep compact secondary rail (current quieting direction) | High |
| D3 | Warnings: local-first vs summary-first? | Local → clearer act; summary-only → miss cause | **Local-first** + compact summary chip | High |
| D4 | Advanced technical info available to normal operators? | Always → leak; never → support pain | Available behind disclosure, not L1 | High |
| D5 | Tabs = full product sections vs progressive wizard? | Tabs match current mental model; wizard changes flow | **Keep three tabs**, fix hierarchy inside | Medium-High |
| D6 | When ACM present, should Fundal lead Montaj over commercial prep? | Lead Fundal → product-first; lead commercial → ERP feel | **Fundal first** when support in composition | High |
| D7 | Confirmare first-paint: open checklist? | Open → longer page; closed → false completion | **Open status + checklist** | High |

## 34. Screenshots

Indexed in `SCREENSHOTS.md` under `screenshots/`.

## 35. Honest visual opinion

Desktop is still ERP-stressful after letter pilot quieting. Product does not dominate. Montaj/Iluminare look assembled. Positive path feels like failure. Implementation should be a presentation reset, not spacing tweaks. Confidence this audit explains the pain: high. Confidence of any “pretty” claim without owner visual GO: none.

## 36. Files modified

Only under:
- `docs/qa/intake-v6-desktop-ui-reset-2026-07-19/**`
- `docs/worklog/realignment/2026-07-19_intake_v6_desktop_ui_reset.md`

## 37. Files not modified

All frontend/backend/domain/tests (except docs). Foreign WIP untouched.

## 38. Worklog

`docs/worklog/realignment/2026-07-19_intake_v6_desktop_ui_reset.md`

## 39. Commit

Docs-only: `docs(intake-v6): reset and explain desktop ui hierarchy` (hash after commit).

## 40. Metoda de lucru si logica abordarii

Operator-goal-first → live visual truth → code ownership map → classify every surface → stress/orphan/nesting audits → hierarchy levels → composition proposal → owner decisions → stop before code.

## 41. Roadmap awareness checkpoint

| Item | Note |
|------|------|
| Nota | 9/10 for audit completeness |
| Închide | Explanation debt before redesign |
| Înghețat | Functional pilot `9f0efa0` + wiring truth |
| Employee Mobile | final-final — out of scope |

## 42. Dead pieces check

- Unmounted SupportContourGeometryCard  
- Confirm handoff blocker props unused  
- Dual Iluminare field owners  
Documented; not deleted in this pack.

## 43. Cat sunt in directia stabilita

Cat sunt in directia stabilita: **88/100%** (audit complete; visual reset not yet implemented — correctly blocked).

## 44. Can implementation start?

**NU** — prerequisites:

1. Owner reviews this pack.  
2. Owner answers decision table D1–D7 (or accepts recommendations).  
3. Explicit owner GO for one coherent presentation implementation build.  
4. Functional baseline remains `9f0efa0` unless a regression forces reopen.

## 45. Next recommended build

One coherent build after GO: **Intake V6 desktop presentation reset v1** — apply hierarchy + composition contracts to Page2 (Finisaje/Iluminare/Montaj) + Confirmare first-paint + stress demotion, without touching frozen domain/pricing/wiring.
