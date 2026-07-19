# Orphaned Text and Ownership Audit

**Marks:** `ORPHANED_UI_ELEMENT` · `DETACHED_HELPER` · `FALSE_URGENCY` · `NESTING_NOISE` · `UNEXPLAINED_DECISION`

## Detached / orphaned findings

| ID | Surface | Text / control | Owner (truth) | Current visual owner | Drift reason | Mark | Belongs | Visible? |
|----|---------|-----------------|---------------|----------------------|--------------|------|---------|----------|
| O01 | Page2 banner | “Următorul pas este în footer” | Guidance model | Blocker banner mid-page | Banner invented navigation hint instead of pointing to owning CTA | `DETACHED_HELPER` | Footer only OR beside Confirmă CTA | Contextual |
| O02 | Finisaje | “Finisaje pe layer. Față, cant și Vector Logo — același card compact pe strat.” | Letter anatomy UX | Floating under tabs | Section intro without card ownership | `DETACHED_HELPER` | Letter groups header | One line under Finisaje tab |
| O03 | Iluminare | Contract fields “Tip iluminare” + “PSU selectat (W)” above specialized section | FinishSetup lighting + contract renderer | Generic contract section floating | Dual renderers: contract + `IntakeV6ReviewLightingSection` | `UNEXPLAINED_DECISION` + duplicate | Single lighting decision group | Always when LED in scope |
| O04 | Iluminare | Helper “Tip iluminare și PSU — câmpuri generice + adapter iluminare specializat.” | Developer note | Above contract fields | Engineering comment leaked to operator | `ORPHANED_UI_ELEMENT` | Technical disclosure | Hide from L1 |
| O05 | Iluminare | “Alege sistemul LED; rezultatele calculate apar separat.” | Lighting UX | Under section title | OK if section owns it | Mild detach | Keep under LED master | Keep |
| O06 | Montaj top | “Activare și arie șablon — responsibility sablon_montaj…” | Modular contract | Above checkbox | Contract ownership string leaked | `ORPHANED_UI_ELEMENT` | Technical disclosure | Hide |
| O07 | Montaj | Cable helper “Pas 2.5 m · 2.5–25…” | Commercial prep | Under cable select | OK locally | — | Under cable | When prep active |
| O08 | Montaj | “Colt service: relevant doar pentru panou ACP…” | ACP process | Grid cell beside cable | Shown when Metal Premount path; not ACP | `DETACHED_HELPER` | Only when ACP selected | Conditional |
| O09 | Montaj | Inactive site note empty box | Scope truth | Nested card | Empty-state card still bordered | `NESTING_NOISE` | Collapse when inactive | Hidden when N/A |
| O10 | Montaj ACP | Dimension source + hash IDs | SVG / geometry truth | Inside cyan nested box | Debug identity on L1 | Technical leak | Disclosure | Hide L1 |
| O11 | Montaj | “Product System” badge/link | Template registry | Header of solution panel | Admin deep-link in operator path | Technical leak | Disclosure | Optional advanced |
| O12 | Pricing rail | Long English/RO analyzer confirm sentence | Composition gate | Rail body | Commercial surface owns product gate message | `DETACHED_HELPER` | Produs card | Quiet one-liner on rail OK |
| O13 | Pricing | “Estimare după configurația curentă…” | Commercial UX | Rail subtitle | OK | — | Rail | Keep quiet |
| O14 | Save footer | “Preturi si materiale actualizate” | Autosave | Review save strip | Success styled near amber pending | `FALSE_URGENCY` if amber | Near save | Success tone |
| O15 | Page1 handoff | Cyan summary “use footer” | Navigation | Side rail | Action in footer, summary in rail | `DETACHED_HELPER` | Footer CTA | Merge |
| O16 | Confirmare | Entire checklist behind collapsed accordion | Confirm truth | Default collapsed | Technical accordion reused for primary page | **Critical orphan of page purpose** | First paint | Always visible summary |
| O17 | Code dead | `IntakeV6SupportContourGeometryCard` | Support contour | Not rendered | Orphaned implementation | `ORPHANED_UI_ELEMENT` (code) | N/A runtime | Remove or wire later — not this audit’s implement |

## Floating between columns

| Observation | Evidence |
|-------------|----------|
| Helper between left decisions and right pricing | Composition confirm message on rail while CTA on left |
| Full-width selects for short enums | PSU watts, template material, ACM thickness — visual weight > importance |
| Labels without card while siblings have 3 frames | Contract iluminare fields sit bare; letter anatomy heavily carded |

## Ownership rule (proposal)

Every string must attach to exactly one of:

1. A control (label/helper under input)  
2. A decision group header  
3. The single guidance spine (footer)  
4. Technical disclosure  

If it matches none → orphan → hide or rewrite.
