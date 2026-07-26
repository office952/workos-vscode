# Contradictions and Dead Pieces

## Contradictions (proven)

1. **Commercial scope none + template enabled + ACM solution present**  
   API: `mounting_scope=none`, `mounting_template_enabled=true`, ACM `mounting_solution` present.  
   Pricing gates sablon off; PD composition blocks with `MOUNTING_SCOPE_INACTIVE` while freezing ACM solution.

2. **UI segmented “confirmat” vs API `PROPOSED`**  
   Probe snippets: „Ansamblul din mai multe panouri a fost confirmat.”  
   API slice: `segmented_background.status = PROPOSED`.  
   Electrical editors shown as if assembly authoritative.

3. **Service corner**  
   UI: under segmented flow, „Colțul service unic nu se mai configurează aici.”  
   Aggregate: `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` with corner null.

4. **Accesorii Tarife lipsă vs Montaj scope**  
   Banner implies Montaj pricing gap; field is manufacturing 5% consumable independent of `mounting_scope`.

5. **Dry-run vs UI Accesorii**  
   Priced dry-run commercial_line_items omit Accesorii row; UI still shows Tarife lipsă Accesorii (live calc / logical path divergence).

6. **Capture ready vs Aggregate blocked**  
   Runtime capture marks mounting_scope/solution ready_for_product_truth; Aggregate composition graph blocked.

7. **Metal trigger mismatch**  
   Aggregate warning: dossier `metal_support_required` vs Intake `mounting_system`.

8. **Confirmare navigation**  
   „Continuă la Confirmare” left URL on operator in recapture — UI affordance vs route behavior.

## Dead / leftover pieces

| Piece | Status |
|-------|--------|
| Legacy `mounting_system` / `mounting_bar_profile` | Compatibility fallback; not canonical readiness |
| Segmented under `mounting_solution.configuration` | Legacy read path |
| `svg_support_selection` adapter | Live dual with bindings |
| Stale doc `ACP_INTERNAL_FRAME_SOURCE_MAP.md` | Doc drift vs nested frame |
| Empty commercial option „Fără soluție suplimentară (șablon montaj)” while ACM product active | Label conflates template aid with product support |

## Duplicate truth paths

- Commercial scope vs product ACM activation  
- Service corner ×3 sources  
- Segmented status UI vs payload  
- Accesorii in material breakdown / logical list / UI banner vs dry-run lines  
- Task preview catalog vs Aggregate task_contract  

## Wrong visibility / labels

- Template fields conceptually commercial but persist with scope none  
- Technical template ID in operator Fundal  
- „Montaj” tab name for product structure  
- Accesorii named as if Montaj decision  

## Plugin logs

No Sentry/Datadog. No hidden exception store consulted.
