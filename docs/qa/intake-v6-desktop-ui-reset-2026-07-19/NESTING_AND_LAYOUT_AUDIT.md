# Nesting and Desktop Layout Audit

**Viewport audited:** 1440×1000 (narrow check 1100×900)  
**App shell:** left nav ~240px + main + optional right rail ~340–360px

## Nesting depth by area

| Area | Visual depth | Component depth | Same ownership frames? | Verdict |
|------|--------------|-----------------|------------------------|---------|
| Page1 preview card | 2 | FileConfirm → canvas | 1 meaningful | Acceptable |
| Page1 layer cards | 2–3 | Decision band → card → details | Advanced legend nested OK | Acceptable |
| Page2 Produs | **4** | Panel → component cards → details → technical accordion | Component cards + technical = dual frames for same composition | `NESTING_NOISE` |
| Page2 scope | 1 | Compact strip | OK | Acceptable |
| Page2 blocker banner | 1–2 | Sticky + expand | OK functionally; too heavy visually | Weight issue |
| Finisaje letter | **3–4** | Tab panel → letter section card → group card → zone | Zone needs ownership; outer section card often redundant | Reduce 1 frame |
| Iluminare | **3** | Contract section card + ReviewSectionShell + lighting card | Dual systems for same lighting | Merge |
| Montaj commercial | **4** | Tab → SectionShell → cardCompact → accordion → inner prep/site cards | Prep/site cards empty still bordered | Collapse inactive hard |
| Montaj Fundal | **5** | Shell → solution panel → cyan ACP box → field grid → segmented/electrical | Deepest operator path | Cap at 3 visual frames |
| Pricing rail | 2 | Sticky shell → panel → details sheet | OK after quieting | Acceptable |
| Confirmare | 2 but collapsed | Page → technical accordion → dashboard | Primary content wrongly nested as “technical” | Structural failure |

## Redundant chrome

| Chrome | Where | Meaning duplicated |
|--------|-------|--------------------|
| Border + bg + title | Almost every subsection | Same “this is a group” |
| Status chips | Produs + banner + footer + drawer | Same incomplete state |
| Padding stacks | Montaj accordion interiors | Vertical bloat |
| Headers | “Montaj” shell + “Montaj comercial” + “Pregătire” | Three titles for one commercial concern |

## Desktop width usage

| Observation | Detail |
|-------------|--------|
| Content max | Review grid `1fr + 300–360px` — left column under-uses wide monitors |
| Empty horizontal | Large dark gaps beside short fields; ACP grid OK at 3-col |
| Long selects | Full-row selects for 3–7 options waste width |
| Alignment | Scope / banner / tabs share left column; pricing sticky right — good bones |
| Above-fold | On 1000px height: Produs + banner + tabs consume fold; **letter decisions often below fold** |
| Scroll length | Montaj ACM path is very long; Iluminare has empty lower third |
| Footer height | Dual bars (status + nav) steal ~120–160px continuously |
| Narrow 1100 | Rail stacks / compresses; stress banners still dominate |

## Empty space explained

| Empty region | Cause | Keep? |
|--------------|-------|-------|
| Below Iluminare dual selects | Contract fields only; specialized section below fold / partial | Fill with decision+results composition or collapse empty |
| Inactive Montaj site card | Empty-state still allocated card height | Collapse |
| Between tabs and first letter group | Intro helper + section chrome | Tighten |
| Right rail lower half | Commercial adjustments collapsed | OK if intentional secondary |

## Nesting policy (proposal)

- Max **3** visible frames from page → input.  
- Inactive groups: **no bordered empty card**.  
- Status: **one spine**, not four chips.  
- Technical IDs: **zero** L1 frames.
