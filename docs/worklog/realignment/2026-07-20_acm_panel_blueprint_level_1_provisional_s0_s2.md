# AcmPanel Blueprint L1-P S0–S2 — worklog

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `3ac9fb96a3ef8d486abfc21547d43063a560ff6e` (`3ac9fb9`) |
| Mode | L1-P only — no L1-C pretence |
| Fixture | `IV6-DB2F86B7` |

## Plan Mode

1. Branch/HEAD confirmed on feature branch after commit-semantics docs.
2. Types: `acmPanel/types.ts`, `segmentedBackground.ts`, `resolveInstance`.
3. SVG reuse: preview canvas exists; new schematic SVG built from mm read model (no SVG-unit bbox).
4. Read model contract: `AcmPanelBlueprintReadModel` in `blueprintReadModel.ts`.
5. Coordinate system: mm, origin top-left assembly, +X right, +Y down.
6. Readiness: L0 / L1-P / L1-C / L1-B only.
7. Authority styling: solid_final / solid_subtle / dashed_proposed / dashed_catalog.
8. Negative fixtures: covered in vitest + config-region letters-only.
9. Renderer test matrix: preview + config integration tests.
10. Inspector: sticky collapsed slot beside inspector (`xl` side column).
11. Screenshot matrix: `docs/audits/_evidence/2026-07-20_acm-panel-blueprint-l1-p/shots/`.
12. Commit: single coherent commit preferred.

## Capability inventory

| Cap | Status |
|-----|--------|
| Repo/code search | USED |
| TypeScript / Vitest | USED |
| Browser/Playwright | USED |
| Runtime API | USED (`:8003`) |
| SVG utilities | USED (pattern only; new mm schematic) |
| Screenshots | USED |
| Subagents | NOT USED this build |
| Figma | **NOT USED — NOT NEEDED** |
| 21st.dev | **NOT USED — NOT NEEDED** |

## Assembly calculation

Multi-panel: panel extent → compare `assembly_dimensions` (tol 1 mm) → never single-contour envelope. Fixture → **2000×350**.

## Zero-write proof

`network-proof.json`: expand/collapse/hover/refresh → **0 PUT**. `pass: true`.

## Roadmap

Owner review → optional L1-C after operator confirms association/technical/segmented/critical fields + composition honesty.
