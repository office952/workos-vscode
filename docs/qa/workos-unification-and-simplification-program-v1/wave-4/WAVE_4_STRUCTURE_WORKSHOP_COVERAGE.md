# Wave 4 gap closure — structure workshops

Dedicated routes under `/product-system/products/:templateCode/structure/*`.  
Do not save. Composer local toggle not clicked.

## Inventory

| ROUTE | SURFACE | PURPOSE | STATUS |
|-------|---------|---------|--------|
| `…/TPL-VOLUMETRIC-LETTERS_v2/structure/vizual-fata` | Letters face docs | Face visual / CNC teaching | **LIVE** (evidence display) |
| `…/volum-aluminiu` | Letters volume docs | Aluminum volume profile | **LIVE** |
| `…/capac-spate` | Letters back docs | Back cap (Forex) | **LIVE** |
| `…/sistem-led` | Letters LED docs | LED system | **LIVE** |
| `…/conexiune-litere-acm-preturi` | Connection price sheet | Teaching / owner-decision display | **WORKSHOP** |
| `…/composer-litere-acm` | Composer IA mock | Study composite; no CostEngine/DB | **EVIDENCE_ONLY** |
| `…/TPL-ACM-BOXED-MOUNTING-SUPPORT_v1/structure/corp-casetat` | ACM boxed body | Canonical ACM step | **LIVE** |
| `…/structura-metalica` | ACM metal frame | Canonical ACM step | **LIVE** |
| `…/structure/fata-panou` (legacy slug) | Redirect | → `corp-casetat` | **LEGACY** redirect |
| `/product-system/products/:code` structure hub | `ProductSystemStructureReadonlyPanel` | Map + links | **LIVE** (Wave 4 initial) |
| `?ps_legacy=1` owner-answer panels | Truth / FACE / FINISH / RETURN-CANT workshops | Embedded on legacy editor | **WORKSHOP** — captured hub only; inner OWNER_INPUT_REQUIRED states **STATE_NOT_REACHED** (would require fixture status / no save) |
| Composition authoring PATCH | `TemplateCompositionAuthoringPanel` | Writes module links | **LIVE authoring** — not traversed (mutation) |

## Exhaustion

Gap-closure RT (`runtime/rt-gap-closure-log.json`): 8 dedicated workshops × admin light+dark, all `FULL_VERTICAL_SCROLL=PASS`, container `main.overflow-auto`.

| Route | Light max | Dark max |
|-------|----------:|---------:|
| vizual-fata | 2733 | 2733 |
| volum-aluminiu | 2935 | 2935 |
| capac-spate | 2726 | 2726 |
| sistem-led | 3055 | 3055 |
| conexiune-litere-acm-preturi | 845 | 845 |
| composer-litere-acm | 12 | 12 |
| corp-casetat | 2852 | 2852 |
| structura-metalica | 2160 | 2160 |

`fata-panou` **redirects** to `corp-casetat` (script `ROLE_ALLOWED=NO` is a false path-equality check; destination already exhausted).  
`?ps_legacy=1` landed on Letters v2 hub (max 1709) — owner-answer inner panels not separately opened.

**STRUCTURE_WORKSHOP_SURFACES_TOTAL = 8** dedicated  
**STRUCTURE_WORKSHOP_SURFACES_EXHAUSTED = 8**  
**STRUCTURE_WORKSHOP_MISSING = 0**

Inner owner-answer `OWNER_INPUT_REQUIRED` panels: **STATE_NOT_REACHED** with blocker “requires candidate-module owner-input fixture; save forbidden.”
