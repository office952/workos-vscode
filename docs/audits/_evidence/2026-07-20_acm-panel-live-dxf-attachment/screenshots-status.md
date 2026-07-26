# Screenshots status — live DXF attachment v1

Source: `screenshot-report.json` + `shots/`  
UI: `http://127.0.0.1:3011` · fixture `IV6-DB2F86B7`  
Network during capture: **zero mutating writes** (inspect/expand only)

| # | Shot | Verdict | File / note |
|---|------|---------|-------------|
| 1 | full Intake before upload | PASS | `shots/01-full-intake-before-upload.png` |
| 2 | inspector upload location | PASS | `shots/02-inspector-upload-location.png` |
| 3 | panel selector | PASS | `shots/03-panel-selector.png` |
| 4 | uploading control | PASS | `shots/04-upload-control.png` |
| 5 | measured single-fold | SKIP_BY_POLICY | golden 2000×300 not bound to IV6 2000×350 |
| 6 | measured double-fold | SKIP_BY_POLICY | same |
| 7 | CUT/V measured breakdown | SKIP_BY_POLICY | covered by `runtime-proof.json` |
| 8 | unknown ACI warning | SKIP_BY_POLICY | unit + runtime proof |
| 9 | stale after config change | SKIP_BY_POLICY | runtime proof |
| 10 | replace action | SKIP_BY_POLICY | needs active attachment on matching QA workspace |
| 11 | live-calc measured/unavailable source | PASS | `shots/11-live-calc-source.png` |
| 12 | preview blockers | PASS | `shots/12-preview-blockers.png` |
| 13 | no money in inspector | PASS | `shots/13-no-money-inspector.png` |
| 14 | Confirm continuity | PASS | `shots/14-confirm-continuity.png` |
| 15 | mobile layout | PASS | `shots/15-mobile-layout.png` |
| 16 | full-page final | PASS | `shots/16-full-page-final.png` |

## Opinion

IV6 UI honesty + upload placement are proven. Measured golden UI shots intentionally skipped on IV6 to avoid contaminating the commercial fixture — measurement truth remains in `runtime-proof.json` / pytest.
