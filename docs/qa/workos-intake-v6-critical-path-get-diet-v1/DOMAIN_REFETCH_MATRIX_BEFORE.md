# DOMAIN_REFETCH_MATRIX_BEFORE

Source: `intakeV6ReviewRefetchDomains.ts` @ `57ec613f`

| Dirty domain | Groups (count) |
|---|---|
| lighting | breakdown, pricing, pricedQuote, productionDryRun, productionHandoff, quoteHandoff, taskPreview, orderBoundReadiness (**8**) |
| face_finish | same as lighting (**8**) |
| artwork_finish | same (**8**) |
| backing | same (**8**) |
| mounting | breakdown, pricing, pricedQuote, productionDryRun, productionHandoff, quoteHandoff, taskGeneration, orderBoundReadiness (**8**, taskGeneration instead of taskPreview) |
| template | all **9** |
| commercial_preview | pricing, pricedQuote (**2**) |
| sheet_footprint | all **9** |

Plus eager effects (not domain-mapped): AI assist on analysisReady; logical-list rides breakdown+pricedQuote.
