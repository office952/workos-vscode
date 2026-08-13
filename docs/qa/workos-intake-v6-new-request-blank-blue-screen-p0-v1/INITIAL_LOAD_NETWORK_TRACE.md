# INITIAL_LOAD_NETWORK_TRACE

Workspace: `e994927e-aa90-46b0-bde0-dd34e025e44e` (READ-ONLY)

## Backend direct

| Check | Result |
|-------|--------|
| workspace GET | **200** |
| workspace exists | YES |
| template_code | `TPL-VOLUMETRIC-LETTERS_v2` |
| payload parseable | YES |
| status | `ready_for_quote_preview` |
| svg upload | analyzed |
| layer_role_setup | complete |

## Sibling GETs (all 200 when sampled)

| Endpoint | Status |
|----------|--------|
| workspace | 200 |
| product-system-binding | 200 |
| template-form-contract / form-contract | 200 |
| pricing-input-preview | 200 |
| material-breakdown | 200 |
| priced-quote-dry-run | 200 |
| quote-handoff-preview | 200 |
| logical-list-read-model | 200 (after PQ settle) |
| ai-informational-assist-candidate | 200 |

## Failed initial requests

```text
FAILED_INITIAL_REQUEST = none (API)
```

Blank screen was **not** caused by 4xx/5xx on workspace bootstrap.
