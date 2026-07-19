# UI/UX E2E Audit — Montaj (after truth)

Figma: authenticated but **not** used as field ownership. Visual comparison deferred; runtime leads.

## Visible Montaj experience (ACM, tab selected)

| Element | Why visible? | Relevant now? | Audience | Next to owner? | Too technical? | Duplicated? | Blocks form? | Placement recommendation |
|---------|--------------|---------------|----------|----------------|----------------|-------------|--------------|--------------------------|
| Tab „Montaj / Fundal · carcasă · site” | Page2 plugin tabs | yes | operator | yes | hint mixes domains | — | no | split product vs commercial tabs/sections |
| Helper „Fundal primul · comercial dacă e în ofertă” | composition V2 copy | yes | operator | yes | ok | — | no | keep |
| Montaj comercial accordion | commercial scope | scope=none — low relevance | operator | separate | ok | vs product | no | demote further when none |
| Fundal și carcasă | product shell | **yes primary** | operator | yes | medium | — | no | should lead (does) |
| ACP config card | ACM active | yes | operator | yes | IDs in technical detail | — | no | keep; hide template IDs in operator |
| „Detaliu tehnic · ID șablon: TPL-ACM-…” | debug aid | no for operator | technical | no | **yes** | diagnostic | no | diagnostic drawer only |
| Segmented multi-panel | detected | yes | operator | yes | ok | status text dup | soft | fix status truth |
| „Ansamblul … a fost confirmat” | UI claim | **conflicts API PROPOSED** | operator | misleading | — | repeated in snippet | false confidence | **bug/contradiction** |
| 220V per panel | electrical | if segmented | operator | under Fundal | ok | vs service corner | soft | only when confirmed assembly |
| Local modules panel | applied interface | ACM | operator/tech | yes | explains no price | — | no | keep collapsed |
| Advanced | fixing/corner/legacy | often | mixed | bottom | yes | legacy mounts | process later | keep collapsed |
| Tarife lipsă Accesorii | pricing rail | always-ish | commercial | far from Montaj fields | semi | footer issues | soft | rename / explain not scope |
| Product System (left nav) | app chrome | n/a | admin | — | — | probe false positive | no | ignore for Montaj labels |
| Attention `! 2 probleme` | V2 corner | yes | operator | tab row | ok | footer | no | keep |
| Diagnostic drawer entry | V2 | yes | technical | outside form | ok | — | no | keep |

## Workflow match?

**Partially.** Copy says Fundal first / commercial secondary — matches intent. Reality: commercial template flags persist with scope none; segmented status messaging lies; Aggregate still demands service corner; pricing Accesorii looks like a Montaj failure.
