# BUILD_INTAKE_V4_ANALYSIS_HASH_HYDRATE_FIX

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before fix | `b409346fae7abd9975b0bb859cfc987971887423` |
| Build date | 2026-06-22 |

## Bug observed (real file)

| Field | Value |
|-------|-------|
| Workspace | `a6cb9f56-2d16-4a53-b569-d5fd51cabfe2` / **IV4-46499080** |
| File | `pbl-layere.svg` (manual upload only — **not hardcoded in fix**) |
| Persisted hash | `c674e8a308d02ebd5ab6ad05df3ecefae43cf42c0689d6e66d6b7fe4ad23c09d` |
| Backend analysis | Persisted ✓ |
| UI after reload | Draft quote blocked — *"Analiza SVG nu este salvată…"* |
| ID | **QA-BUG-1** |

## Audit — hash flow

| Concern | Location |
|---------|----------|
| `localFileHash` set on upload | `useIntakeV4Workspace.ts` → `ANALYZER_READY` via `sha256HexFromText(svgSource)` |
| `persistedFileHash` | `getPersistedFileHash(payload)` → `payload.svg_source.file_hash` |
| `hasUnsavedAnalysis` | `intakeV4AnalysisIdentity.ts` — checks `state.unsavedAnalysis`, `localFileHash` vs persisted |
| Upload state | `ANALYZER_START` clears hash; `ANALYZER_READY` sets local hash + `unsavedAnalysis=true` |
| Load/reload hydrate | `intakeV4WorkspaceReducer.ts` → `applyHydratedWorkspace` on `LOAD_SUCCESS` |
| Draft quote hash | `IntakeV4ConfirmStep.tsx` — `state.localFileHash ?? getPersistedFileHash(payload)` |

### Hash fields (do not conflate)

| Field | Semantics |
|-------|-----------|
| `svg_source.file_hash` | **Source of truth** for quote draft guard / `client_analysis_hash` |
| `source_content_hash` | Raw uploaded bytes hash (may match `file_hash`) |
| `analysis_content_hash` | Post-sanitization hash (doctype strip etc.) — **expected ≠ source** |
| Local selected file hash | SHA-256 of in-memory SVG text before persist |

**Quote guard must use `svg_source.file_hash`**, not `analysis_content_hash`.

## Root cause

In `applyHydratedWorkspace`, after setting:

```typescript
localFileHash: persistedHash ?? state.localFileHash,
```

`unsavedAnalysis` was computed as:

```typescript
persistedHash == null || state.localFileHash !== persistedHash
```

On fresh reload `state.localFileHash` is `null`, so `null !== persistedHash` → **false positive unsaved** even though hydration assigns the correct hash.

## Fix

1. Added `resolveHydratedFileHashSync()` in `intakeV4AnalysisIdentity.ts`:
   - If persisted hash exists and no local mismatch → set `localFileHash = persisted`, `unsavedAnalysis = false`
   - If local hash differs from persisted → keep local, `unsavedAnalysis = true` (new file selected)
   - If no persisted hash but local exists → unsaved

2. Updated `applyHydratedWorkspace` (both full hydrate and fallback branches) to use the helper.

## Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/intakeV4/intakeV4AnalysisIdentity.ts` | `resolveHydratedFileHashSync` helper |
| `frontend/src/lib/intakeV4/intakeV4WorkspaceReducer.ts` | Fix hydrate unsaved logic |
| `frontend/src/lib/intakeV4/intakeV4AnalysisIdentity.test.ts` | New unit tests |
| `frontend/src/lib/intakeV4/intakeV4WorkspaceReducer.test.ts` | QA-BUG-1 regression tests |
| `docs/qa/BUILD_INTAKE_V4_REAL_FILE_PRODUCTION_DECISION_TEST_PACK.md` | QA-BUG-1 fix reference |
| `docs/qa/BUILD_INTAKE_V4_ANALYSIS_HASH_HYDRATE_FIX.md` | This doc |

## Hash source of truth

```typescript
getPersistedFileHash(payload) → payload.svg_source.file_hash
```

Same field used by backend hash sync guard for `create-draft-quote`.

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4AnalysisIdentity.test.ts src/lib/intakeV4/intakeV4WorkspaceReducer.test.ts src/lib/intakeV4/intakeV4Readiness.test.ts
```

Result: **17 passed** (2026-06-22)

Coverage:

1. LOAD_SUCCESS with `svg_source.file_hash` hydrates `localFileHash`
2. `hasUnsavedAnalysis=false` after reload with persisted analysis
3. New local file selection → `unsavedAnalysis=true`
4. PERSIST_SUCCESS → `unsavedAnalysis=false`
5. `getPersistedFileHash` uses `file_hash`, not `analysis_content_hash`
6. Real hash mismatch still blocks

## Retest instructions (IV4-46499080)

1. Hard refresh: http://127.0.0.1:3000/intake-v4-app/a6cb9f56-2d16-4a53-b569-d5fd51cabfe2/operator
2. **No re-upload** required if fix is complete
3. Confirm draft quote button enabled (or hash blocker gone)
4. Create draft quote; verify `client_analysis_hash` = persisted `svg_source.file_hash`
5. Confirm no ExecutionPlan / tasks_json created

## No hardcode confirmation

- No filename checks
- No hash literals in application code
- Generic helper + reducer logic only

## PASS / FAIL

| Check | Result |
|-------|--------|
| Automated tests | **17 passed** (AnalysisIdentity + WorkspaceReducer + Readiness) |
| Manual retest IV4-46499080 | **PASS** — hard refresh, no re-upload; `READY_FOR_QUOTE_PREVIEW`; no unsaved-analysis message; draft quote button **enabled** after confirm checkboxes |
| ExecutionPlan / tasks_json | **NO** (not created by this build) |
| **Build verdict** | **PASS** |

## Commit recommendation

Recommend commit after manual retest PASS on IV4-46499080 without re-upload.
