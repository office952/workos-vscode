# RUNTIME-FRESHNESS-04B — Ambiguous process fail-closed correction

## 1. Status

**COMPLETE** — `RUNTIME_FRESHNESS_04B_AMBIGUOUS_PROCESS_FAIL_CLOSED_COMPLETE`

Interrupted changes **recovered** from working tree (not recreated from scratch).

## 2. Starting HEAD

`c2ceaf9`

## 3. Owner review reason

04A independent review: all-uvicorn `ambiguous` ownership could still reuse when health + OpenAPI manifest routes passed. Violates R3–R5: only proven `same_worktree` may reuse or be stopped automatically.

## 4. Parallel research workstreams (pre-interruption)

| Stream | Finding |
|--------|---------|
| A — Ownership audit | Reuse at lines 597–602 + bypass 494–507 |
| B — Windows evidence | Listener exe is system-python; venv proof on parent chain |
| C — Contract gap | No test blocked ambiguous + routes valid |

## 5. Ambiguous reuse root cause

Explicit `allUvicornAmbiguous` exception allowed ambiguous trees to reach health/OpenAPI; `onlyWorkOsUvicornTree` granted `Ready=$true` without `same_worktree`.

## 6. Ownership evidence

- Primary: `.venv\Scripts\python.exe` under `ProjectRoot` in executable or parent cmdline
- Windows reload: `Test-WorkOsBackendProcessParentLineageProof` walks ancestors for venv or canonical launcher scripts under `ProjectRoot`
- Spawn workers inherit proven parent

## 7. Final decision matrix

| Ownership | Fresh | Action |
|-----------|-------|--------|
| same_worktree | yes | reuse |
| same_worktree | stale routes | controlled_stop |
| other_worktree | any | BLOCK |
| foreign | any | BLOCK |
| ambiguous | any | BLOCK |

OpenAPI cannot upgrade ownership.

## 8. Files changed

| File | Change |
|------|--------|
| `scripts/_workos-dev-backend-freshness.ps1` | Fail-closed ambiguous; parent-lineage proof; stop targets restricted |
| `scripts/canonical_startup_contract.test.mjs` | +10 tests (36 total) |
| `.compound-engineering/.../compound-knowledge.md` | 04B update |
| This worklog | New |

## 9. Contract tests

`npm run test:startup-contract` → **36/36 PASS**

## 10. Runtime verification

| Check | Result |
|-------|--------|
| Classification | `same_worktree` / `current_and_ready` |
| Health | 200 |
| Manifest routes | 5/5 |
| Live GET 23099 | 200, 13 tasks, contract v1 |
| Stability | health 200, 1 listener |
| Backend PID | 33552 |
| Frontend PID | 35880 |

## 11. Second-start reuse

```
Backend already running (freshness=current_and_ready, PID=33552)
All services already running - no duplicate processes started.
listeners_before=1 listeners_after=1
```

## 12. DB verification

Live GET before/after mtime identical → **0 operational writes**.

## 13. Independent review

- Reviewer independent: **YES** (Bugbot)
- Verdict: **APPROVE_WITH_EXPLICIT_LIMITATION**
- Finding: parent-lineage trusts launcher ancestry under `ProjectRoot` when listener exe is system-python — documented limitation; does not violate R3–R5 (ambiguous/foreign/other still blocked)

## 14. Compound knowledge

`.compound-engineering/runtime-freshness-04-canonical-backend-route-guard/compound-knowledge.md`

## 15. Blocked scope

No backend app, DB, UI, Product System, snapshots, FLEX-02.

## 16. Commit

`fix(runtime): block ambiguous backend process reuse` — pending user-requested `/ce-commit`.

## 17. What remains

Optional: stricter listener-level venv executable proof if owners reject lineage heuristic.

## 18. Next safe step

**OWNER REVIEW RUNTIME-FRESHNESS-04B**

## 19. Direction score

**90/100** — Owner policy enforced; canonical startup works via parent-lineage on Windows reload.
