# Intake V6 — Status Semantics Normalization

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `a657600` (status semantics audit)  
**Mode:** Presentation normalization only — no layout / backend / contracts

## Verdict

**PASS** — one canonical status vocabulary drives primary Intake V6 status labels. Internal domain values unchanged.

## Canonical set

| Semantic | RO label |
|----------|----------|
| proposal | Propunere |
| needs_operator | Necesită confirmare |
| missing_data | Lipsă date |
| warning | Avertizare |
| blocker | Blocant |
| owner_decision | Decizie administrator |
| confirmed | Confirmat |
| ready | Pregătit |

Plus presentation helpers for `rejected` / `inactive` / `informational` where domain already used them.

## Single helper

`frontend/src/lib/intakeV6/intakeV6OperatorVocabulary.ts`

- `operatorStatusSemanticRo`
- `resolveOperatorStatusSemantic`
- context helpers: finish cards, artwork, Page 1 icon vs text, segmented, electrical assembly, confirm indicator, workspace ready

Rule: **internal state → semantic → RO label → UI** (no per-tab duplicate maps).

## Mapping applied

| Before | After | Meaning preserved |
|--------|-------|-------------------|
| OK (Finisaje) | Confirmat | finish confirmed |
| Lipsă (missing color) | Lipsă date | required field missing |
| Lipsă (artwork unconfirmed) | Necesită confirmare | action required |
| Confirmat in Pasul 1 | Necesită confirmare | finish still open |
| De confirmat (icon / role unknown) | Necesită confirmare | operator action |
| Propunere (Page 1 text) | Propunere | analyzer proposal (kept distinct) |
| Propus | Propunere | segmented PROPOSED |
| Draft / neconfirmat | Necesită confirmare | electrical assembly badge |
| UNCONFIRMED (select option) | Neconfirmat | domain config noun (kept) |
| Totul OK / detail OK | Pregătit | ready ≠ confirmed |
| Blocat / Blocată | Blocant | blocker |
| Atenție (confirm indicator) | Avertizare | warning |
| OWNER_GATE_REQUIRED | Decizie administrator | owner decision |
| Necesită verificare tehnică (guard) | Avertizare | soft guard |

## Surfaces touched

- Page 1: status icon aria, operator panel badge, role table confirmation text, binding suggested, guarded
- Finisaje: letter + artwork badges
- Confirmare: consolidated indicator
- Segmented: `statusLabelRo` + Montaj cluster badge (label only)
- Electrical: assembly badge
- Header: aggregate + SVG/pricing ready values
- System checks badges
- ACP owner-gate intro line

## Frozen / untouched

- Montaj IA structure (label-only where segmented status contradicted)
- Segmented / electrical contracts
- Analyzer, PD, Aggregate, backend, schemas, pricing, Execution
- Page 1 / composition layout

## Tests

Targeted Vitest: **83 passed** (vocabulary, badges, header, confirm, segmented, electrical, Finisaje artwork, Page 1 table, system checks).

## Screenshots

`screenshots/` — `before_*` from audit pack on same stack (shows old OK/Lipsă/Propus language).  
After labels proven by unit tests + HMR stack FE `:3001` / BE `:8003`. Full live after-pack deferred when no seeded finish workspace was available in-browser (session gate).

## Risks

- E2E string asserts elsewhere may still expect old words (none found under `frontend/e2e` for these tokens).
- Guard label shortened to **Avertizare** — less explanatory; technical accordion still has detail.
- Page 1 keeps **Propunere** (text) vs **Necesită confirmare** (icon) intentionally distinct.
