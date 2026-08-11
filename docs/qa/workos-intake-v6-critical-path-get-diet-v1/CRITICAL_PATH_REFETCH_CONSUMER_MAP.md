# CRITICAL_PATH_REFETCH_CONSUMER_MAP

**GO:** `AUTHORIZE_WORKOS_INTAKE_V6_CRITICAL_PATH_GET_DIET_V1`  
**Baseline:** `57ec613f`

## Group consumers

| Group | Consumer | Step 2 visible? | Hidden? | Diagnostic? | Production? | Confirm-only? | Live price? | Save success? | Lazy? | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| breakdown | LiveCalculationSummary rail + material panel | Y (rail) | material drawer | N | N | N | Y | N | keep eager | **A** |
| pricing | Live rail / slider defaults | Y | sliders collapsed | N | N | N | Y | N | keep eager | **A** |
| pricedQuote | Official Ofertă on rail; Confirm reloads own | Y | N | N | N | N | Y | N | keep eager | **A** |
| quoteHandoff | Banner / readiness / blockers | Y | also in drawer | N | N | N | N | N | keep eager | **A** |
| productionDryRun | ProductionTaskDryRunPanel | drawer only | Y | Y | Y | N | N | N | **on drawer open** | **E** |
| productionHandoff | ProductionHandoffPreviewPanel | drawer only | Y | Y | Y | N | N | N | **on drawer open** | **E** |
| taskGeneration | TaskGenerationDryRunPanel | drawer only | Y | Y | Y | N | N | N | **on drawer open** | **E** |
| taskPreview | Task catalog in drawer | drawer only | Y | Y | partial | N | N | N | **on drawer open** | **D** |
| orderBoundReadiness | OrderBound + commercial spine in drawer | drawer only | Y | Y | Y | N | N | N | **on drawer open** | **E** |

Confirm (`useIntakeV6FinalHandoff`) loads its own: binding, breakdown, nesting, pricing, pricedQuote, quoteHandoff — **not** production/task/order-bound.

## Debounce (unchanged this slice)

| Path | ms |
|---|---|
| selector autosave short | 700 |
| selector autosave long | 1400 |
| commercial slider timer | 700 |

Selector vs free-text policy left in place; GET diet is the latency win without risking save races.
