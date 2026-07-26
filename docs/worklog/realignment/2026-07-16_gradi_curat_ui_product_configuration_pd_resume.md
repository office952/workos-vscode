# 2026-07-16 Gradi-curat UI product configuration + PD resume

Task: `WORKOS-GRADI-CURAT-UI-PRODUCT-CONFIGURATION-AND-PD-RESUME-V1`  
HEAD: `b3eb437`  
Verdict: **GRADI_CURAT_UI_FIRST_BLOCKER_FOUND**

## Exact URL

`http://127.0.0.1:3000/intake-v6/11891d68-c4c8-4719-acc5-f8fcb22a44af/operator`  
Visible code: `IV6-5A24B7B0`

## SVG hash

Expected `593C4D43…AB6CF1` — API match YES (case-insensitive). Unchanged.

## Owner answers G1–G6

See `docs/qa/gradi-curat-e2e/ui-walkthrough/owner_answers_G1_G6.md`.

## UI actions performed

| # | Page/section | Control | Value | Result |
|---|--------------|---------|-------|--------|
| 1 | Straturi | visual verify | file/dims/layers/composition | PASS visible |
| 2 | Configurare / Finisaje | letter cards | face=`none`, cant Alb 60 mm already | accepted (no vinyl) |
| 3 | Configurare / Finisaje | logo cards | Print+laminare already | accepted for G4 |
| 4 | Configurare / Finisaje | Finisaj spate | **only Forex options** | **cannot set none** |
| 5 | Iluminare | Culoare lumina | Cool white | set; auto-sync |
| 6 | Iluminare | LED activ | checked (FRONT_LIT) | left ON |
| 7 | Montaj | Scope | Pregătire + montaj la locație | set; site install ON |
| 8 | Montaj | Șablon | checked | kept |
| 9 | Montaj | Soluție | Fără soluție suplimentară (no ACM) | kept |
| 10 | Confirmare | Continuă | **not clicked** | stop before claiming ready |

## Persisted finish_setup (after auto-sync)

- `illuminated=true`, `light_color=cool`
- `face_finish_type=none`, `return_finish_type=white_aluminum`, `return_depth_mm=60`
- `mounting_scope=preparation_and_site_installation`, `site_installation_included=true`
- `backing_mode=forex_10_no_bevel` ← **violates owner “fără Forex continuu”**; UI cannot clear it
- `mounting_solution=null` → adapter `MOUNTING_SOLUTION_MISSING`
- readiness: `runtime_capture_blocked`

## ProductDefinition

Preview builds with workspace payload. Not commercially ready while runtime capture blocked and forced Forex contradicts owner.

## First next blocker

**INTAKE_UI:** `backing_mode=none` exists in type/tests as deliberately **not exposed**; select only Forex 10 mm. Owner requires no continuous Forex/ACM plate. API injection forbidden.

Secondary: `runtime_capture:MOUNTING_SOLUTION_MISSING` even with “Fără soluție suplimentară”; plexiglas opal 3 mm / alb mat / laminare mată not first-class discrete UI fields beyond finish enums.

## Recommended next action

**correct one coherent Intake UI/contract blocker** — expose `backing_mode=none` (no continuous letter back plate) and map mounting_solution empty-state so runtime capture clears without ACM.

## Forbidden paths

Browser UI used; same workspace/hash; no new workspace; no quote/order; no API finish injection for backing=none; no product code; no SVG change.

## Direction

Score 7/10 · Cat sunt in directia stabilita: **72/100%**
