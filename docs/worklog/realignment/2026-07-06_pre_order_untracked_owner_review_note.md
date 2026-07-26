# Pre-order Untracked Files - Owner Review Note

## Verdict
KEEP_FOR_OWNER_REVIEW

## Current HEAD Safety

- HEAD: `9fd0f92`
- HEAD frontend pre-order refs: NO
- ReviewStep dirty: NO
- ConfirmStep dirty: NO
- Clean checkout risk: NO

## What These Files Are
Aceste fisiere sunt ramasite locale/untracked pentru `pre-order technical preview` si `component-task composition preview`.

Ele par gandite ca preview read-only, dar nu sunt parte din HEAD si nu sunt folosite de flow-ul activ.

## Why They Are Not Committed Now

- Nu sunt necesare pentru analyzer-first Product Truth.
- Nu sunt necesare pentru Gradi letters + logo composition.
- Nu sunt necesare pentru ProductDefinition-ready payload acum.
- Sunt downstream-adjacent.
- Folosesc vocabular apropiat de task/composition/execution/pre-order.
- Backend routerul poate deveni live local prin auto-discovery daca este inclus.
- Owner GO explicit este necesar pentru orice commit pre-order.

## Why They Are Not Deleted Now

- Pot fi utile pentru un slice separat ulterior.
- Exista indicii read-only si teste asociate.
- Stergerea trebuie facuta doar dupa owner GO.
- Nu se foloseste `git clean -fd`.

## Known Local Groups

- Backend router/service/schema/adapter/tests
- Frontend API/display helpers/panels/summary/tests
- Docs architecture/QA/worklog/export

## Safety Notes From Audit

- Backend endpointul pare GET-only.
- Frontend API foloseste fetch fara method/body.
- Panels par display-only.
- Copy-ul mentioneaza read-only / no tasks / execution / stock / assignments.
- Schema/adapter folosesc flag-uri no-write/no-taskgraph/no-quote-order mutation.
- Totusi feature-ul ramane downstream-adjacent si necesita owner GO.

## Owner Decision Later
Optiuni:

1. Keep for future owner-reviewed slice
2. Cleanup local files after owner GO
3. Archive remnants after owner GO
4. Commit separate read-only preview only with owner GO and QA

## Explicit Forbidden Until Owner GO

- no commit of pre-order files
- no ProductAggregate
- no TaskGraph
- no ExecutionPlan
- no Quote/Order/Execution write
- no seeds/migrations/DB
- no `_tmp_*`
- no `git add .`

## Current Recommendation
Pastreaza temporar fisierele pre-order untracked pentru owner review.
Nu le comite acum.
Nu le sterge acum.
Nu le conecta la analyzer-first lane.
