# Lookup request-volume proof

```text
ExecutionDetail:
task count = 1
lookup requests = 1
Ops-Graph:
node/task count = 1
lookup requests = 1
LOOKUP_REQUEST_PATTERN = VERIFIED_ACCEPTABLE
BULK_LOOKUP_REQUIRED = NO
```

Pattern: `useActiveMachineRunByTasks` — one `GET …/by-task` per unique `(execution_plan_id, task_key)`, cached for the page mount. Typical operator pages (~10–20 tasks) remain bounded; no bulk endpoint required for V1.
