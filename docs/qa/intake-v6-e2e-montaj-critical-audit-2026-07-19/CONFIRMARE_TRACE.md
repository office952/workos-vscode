# Confirmare Trace — Montaj

## Blockers / warnings from Montaj (code)

Source: `intakeV6FinalConfirmationBlockers.ts` + `intake_v4_finish_truth_service.py` mounting_*_runtime_state + process resolver.

| Condition | Severity | Operator message quality | Gates Confirmare? |
|-----------|----------|--------------------------|-------------------|
| Product composition unconfirmed | blocker | Romanian, clear | yes |
| Segmented PROPOSED | warning | clear — confirm/reject in Montaj | soft |
| Segmented validation cutout/insert crossing | blocker | Romanian mapped | yes |
| Segmented electrical unresolved when CONFIRMED | warning | clear | soft |
| mounting_scope missing/unconfirmed | blocker (capture/truth) | may surface as raw code in diagnostic | yes for truth |
| mounting_solution missing when prep active | blocker | raw `MOUNTING_SOLUTION_MISSING` in capture | yes when prep |
| Service corner missing for alucobond | Aggregate/process error | technical Aggregate conflict | blocks Aggregate readiness |
| Accesorii Tarife lipsă | pricing warning | operator-visible | **does not** equal Confirmare ready |

## Runtime ACM

- Composition confirmed earlier.
- Attention chip `! 2 probleme` on Page 2.
- Footer: `1 blocant - 1 avertizare - 7 informații` (from Finisaje-first screenshot).
- Capture read model: mounting_scope + mounting_solution fields `confirmed` / ready_for_product_truth true (scope none still “confirmed” value).
- Aggregate: `COMPOSITION_GRAPH_BLOCKED` + `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED`.
- Playwright „Continuă la Confirmare” did **not** navigate off operator in recapture — Confirmare ready **not** proven.

## Duplication

Blocked state can appear in: attention corner, footer inventory, Confirmare checklist, pricing Tarife lipsă, Aggregate conflicts (diagnostic). Composition correction V2 reduced but did not eliminate multi-surface negatives.

## Screenshot naming honesty

- Do **not** label Confirmare ready.
- Blocked/incomplete only.
