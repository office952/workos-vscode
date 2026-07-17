# Worklog — Cursor SVG vector tooling installation

| Field | Value |
|-------|-------|
| Task | `INSTALL_VALIDATE_DOCUMENT_CURSOR_SVG_VECTOR_TOOLING` |
| Owner GO | explicit |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `dbb9186` |
| Start | `CURSOR_SVG_VECTOR_TOOLING_INSTALLATION_IN_PROGRESS` |
| Final | `CURSOR_SVG_VECTOR_TOOLING_INSTALLED_WITH_GUARDS` |

## Decision

Install and recommend **Better SVG** (`midudev.better-svg` `0.5.1`) as Cursor developer tooling only.  
Do **not** install Visual SVG Editor without a separate owner GO.

## What was done

1. Baseline: HEAD, dirty tree (untouched unrelated WIP), no prior SVG extensions.
2. Supply-chain check: Marketplace + Open VSX verified + Apache-2.0 + official GitHub.
3. Install via `cursor --install-extension midudev.better-svg`.
4. Opened three real SVGs + one TSX with inline SVG; SHA-256 unchanged.
5. Added `.vscode/extensions.json` recommendation only (no aggressive settings).
6. Documented tooling, decision, validation, Analyzer/Alucobond boundaries.

## Deliverables

| Piece | Path |
|-------|------|
| Tooling guide | `docs/tooling/CURSOR_SVG_VECTOR_TOOLING.md` |
| Decision | `docs/decisions/CURSOR_SVG_TOOLING_DECISION.md` |
| Validation | `docs/audits/2026-07-17_cursor_svg_vector_tooling_validation.md` |
| Workspace recommendation | `.vscode/extensions.json` (`.gitignore` carve-out) |
| This worklog | `docs/worklog/realignment/2026-07-17_cursor_svg_vector_tooling_installation.md` |

## Guards

- Preview/zoom UI click not fully automated in Extension Host webview — owner spot-check once.
- SVGO only on explicit Optimize; never on originals.
- Visual SVG Editor deferred.
- No WorkOS runtime authority.

## Dirty-tree protection

Exact-path staging only. Unrelated WIP, SVG assets, and app code left untouched.

## Next safe step

**Option 1 — GO FIX OWNER PROOF ROUTE AND CONTEXT PRESERVATION**
