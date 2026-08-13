# LOGICAL_LIST_AUTHORITY_MAP

Logical-list is a **projection / read model**. It is not commercial authority.

## A. Material Breakdown truth (consumed)

Used for nearly all VL rows:

- materials / quantities / units / estimated cost subtotals
- source part IDs, gaps, warnings
- Oracal / plexiglas / forex / return / LED / PSU / labor / CNC services

Authority: `get_material_breakdown_for_workspace`.

## B. PricedQuote truth (consumed)

Used narrowly:

- `commercial_line_items` filtered to `acm_*` / `letters_acm_conn_*` → composition logical rows
- envelope: workspace_id/code, template_code, `commercial_totals` in runtime_totals chrome

Authority for money remains CPP via sibling pricedQuote for Ofertă.  
LL composition rows are display of commercial lines, not a second price engine.

## C. Workspace / finish truth

- Oracal series / color preferences
- offer-scope filtering
- composition recommendation attach ids
- confirmed face source_part_ids from SVG analysis

## Offer lifecycle

Frontend `deriveIntakeV6OfferLifecycleStatus` does **not** include logical-list loading.  
Official CURRENT can (and already does in code) occur when pricedQuote settles, independent of LL.
