# DOMAIN_REFETCH_MATRIX_AFTER

| Dirty domain | Groups (count) |
|---|---|
| lighting | breakdown, pricing, pricedQuote, quoteHandoff (**4**) |
| face_finish | **4** |
| artwork_finish | **4** |
| backing | **4** |
| mounting | **4** |
| template | **4** |
| sheet_footprint | **4** |
| commercial_preview | pricing, pricedQuote (**2**) |

Production / task / order-bound groups removed from domain map.  
ReviewStep effects for those groups require `diagnosticSectionOpen` (+ refresh on `workspace.updated_at` while open).

Immediate post-save GETs for ordinary finish change: **4** domain groups + logical-list ≈ **5** (meets ≤4–5 target).
