# Validation — Cursor SVG vector tooling

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Task | `INSTALL_VALIDATE_DOCUMENT_CURSOR_SVG_VECTOR_TOOLING` |
| HEAD before | `dbb9186` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Extension | `midudev.better-svg` `0.5.1` |
| Verdict | `CURSOR_SVG_VECTOR_TOOLING_INSTALLED_WITH_GUARDS` |

## Security / supply-chain (minimum)

| Check | Result |
|-------|--------|
| Publisher | midudev / Miguel Ángel Durán |
| Extension ID | `midudev.better-svg` |
| Marketplace | Visual Studio Marketplace (official item) |
| Open VSX | verified publisher; downloadCount ≈ 21k; version `0.5.1`; timestamp `2026-06-19` |
| Repository | https://github.com/midudev/better-svg |
| License | Apache-2.0 (`LICENSE.txt` in VSIX) |
| Dependencies | bundled `svgo@4.0.1` only |
| Activation | language events including `svg`, `typescriptreact`, … |
| Auto-optimize on save | **absent** (Optimize = command only) |
| Telemetry / remote fetch (static scan) | no dedicated telemetry API found; Optimize uses local SVGO + `WorkspaceEdit` |
| Unofficial .vsix | not used — Cursor CLI marketplace install |

## Installation

```text
cursor --install-extension midudev.better-svg
→ Extension 'midudev.better-svg' v0.5.1 was successfully installed.
cursor --list-extensions → midudev.better-svg
```

Inventory before: only `anysphere.remote-ssh`. No prior SVG extension.

## Test files (originals — not modified)

| ID | Path | Role |
|----|------|------|
| A | `fisiere-teste-svg/litere-vol-1-layer.svg` | Litere simple, path-uri multiple, grup layer |
| B | `fisiere-teste-svg/logo.svg` | Simbol polygon + grup `Volumetrice` |
| C | `fisiere-teste-svg/gradi-curat.svg` | Litere color + contururi stroke (candidat chenar/panou) |

Also opened for hover/language activation: `frontend/src/components/workos/intake-v6/IntakeV6NestingPreviewPanel.tsx` (inline `<svg>`).

## Hash before / after (SHA-256)

| File | Before = After |
|------|----------------|
| A litere-vol-1-layer.svg | `381FEDECFCCCBFCC808B5384E389624CCC7FCD71F28D855A2CBBBF588E4DABDC` |
| B logo.svg | `0EEB1BE8D36ED6F5561328439A4EB370806C41AA0203D4C4D58E41951695BEBE` |
| C gradi-curat.svg | `593C4D439157B83CAB16C33D69CAF0AB426144D583FB1999FA7D1676D5AB6CF1` |

Match after open/preview activation in Cursor: **PASS** for all three.  
No auxiliary files created under `fisiere-teste-svg/`.  
`git status` pe fixtures Analyzer: fără modificări pe originale tracked relevante; A/B rămân untracked pre-existenți (nu comise).

## Validation matrix

| Verificare | A | B | C |
|------------|---|---|---|
| Fișierul se deschide | PASS | PASS | PASS |
| Preview vizibil | PASS_WITH_GUARD* | PASS_WITH_GUARD* | PASS_WITH_GUARD* |
| Zoom (webview implementare + UI) | PASS_WITH_GUARD* | PASS_WITH_GUARD* | PASS_WITH_GUARD* |
| Pan | PASS_WITH_GUARD* | PASS_WITH_GUARD* | PASS_WITH_GUARD* |
| Path-urile vizibile în cod | PASS | PASS | PASS |
| ViewBox respectat (în sursă) | PASS `0 0 343.78…` | PASS `0 0 117.30…` | PASS `0 0 519.77…` |
| Width/height / viewBox | PASS (viewBox-driven) | PASS | PASS |
| Transform-uri | N/A (fără transform agresiv) | N/A | N/A |
| Fill/stroke corecte în sursă | PASS fills | PASS stroke polygon | PASS fills + stroke contours |
| Goluri interioare (vizual/cod) | PASS (path-uri litere) | N/A simbol | PASS |
| Contur exterior vizibil (cod) | PASS | PASS | PASS (stroke paths) |
| Fișier nemodificat / hash | PASS | PASS | PASS |
| Fișiere auxiliare | PASS none | PASS | PASS |
| Console / Extension Host | PASS (install OK; no host crash observed) | PASS | PASS |

\*Preview/zoom: validated by (1) opening real `.svg` in Cursor with extension installed and active; (2) official webview `main.js` zoom/pan handlers (`scale`, `wheel`, `mousedown` pan). Agent cannot drive Extension Host webview clicks; owner should confirm zoom once in Explorer → SVG Preview. Guard documented — not a runtime fail.

## Auto-format / Auto-SVGO

| Check | Status |
|-------|--------|
| Auto-SVGO on save | OFF (no such setting; Optimize is command) |
| Format-on-save SVG workspace | not enabled by this task |
| `betterSvg.floatPrecision` applied on open | no |

## Visual SVG Editor

| Check | Result |
|-------|--------|
| Installed | **No** |
| Open VSX | 404 |
| Marketplace | present, early `0.1.0` |
| Recommendation | `VISUAL_SVG_EDITOR_EVALUATION_REQUIRED` + owner GO before any install |

## Workspace recommendation

Added `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "midudev.better-svg"
  ]
}
```

Repo previously ignored all of `.vscode/`. Minimal `.gitignore` carve-out added so only `extensions.json` can be tracked. No `.vscode/settings.json` added (avoid inventing aggressive keys). Recommended keys documented in tooling doc only.

## SVGO copy test

Not run on originals (policy). Manual Optimize remains available on temporary copies only.

## Boundaries confirmed

- No app / Analyzer / Product System / CPP / tasking edits.
- No schema / migration / seed.
- Extension is not presented as analyzer.
- Alucobond direction documented as design intent only.

## Remaining guards

1. Owner one-time UI confirm of zoom in SVG Preview panel.
2. Never Optimize originals.
3. Visual SVG Editor stays out until separate GO.
4. Future Modules/Governance sync notes only (no broad sync now).
