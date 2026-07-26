# External Artwork Analysis Ownership

| Field | Value |
|-------|--------|
| Status | **CANONICAL BOUNDARY** — owner GO 2026-07-20 |
| Date | 2026-07-20 |
| Scope | Permanent ownership split: desktop analysis app vs WorkOS Product System |
| Supersedes (partial) | In-repo SVG/DWG/DXF analysis as a WorkOS product responsibility |
| Related | Operator teaching model; Product System authoring co-design; `artwork_analysis_contract_v1` |

---

## 1. Decision

**External Artwork Analysis Ownership**

| Party | Owns |
|-------|------|
| **Separate desktop application** | All file intelligence: import; SVG / DWG / DXF (and other graphic) analysis; geometry; shapes; text; groups; measurements; layers; classification; auto-grouping; mapping proposals; CAD/vector intelligence |
| **WorkOS** | Product / business / execution truth: families, templates, component contracts, composition, dossier, lifecycle, readiness, publication, Product Truth, PD / Aggregate / Quantity, CPP / EIC, Snapshots, Order, EP preview, authoring UI, provenance, **integration contracts with the desktop app** |

This is an absolute architectural permanent limit. WorkOS must **STOP** implementing or extending internal analysis/parse/interpret of SVG, DWG, DXF, or other graphic files.

---

## 2. Canonical flow

```text
Desktop Analysis App
  → external structured result (observed / proposed only)
  → WorkOS Intake / Product System
  → Operator review
  → Confirm
  → Product Truth
  → PD / Aggregate / Quantity / CPP / EIC / Snapshot / Order / Execution
```

Rules:

1. External result is **never** authority by itself.
2. Only the operator confirms Product Truth.
3. Quantity / PD / Aggregate consume **confirmed** truth only.
4. Snapshot freezes confirmed revision + analysis **reference/hash** — never re-reads the desktop app at freeze.
5. Transport (HTTP / file / folder / sync) is **TBD** — separate decision; not required to freeze this boundary.

---

## 3. WorkOS role

WorkOS is consumer, reviewer, confirmer, and persister:

- **Consume** a versioned external payload (`artwork_analysis_contract_v1`).
- **Validate** structure, contract version, provenance fields.
- **Present** observations and suggested bindings for operator review.
- **Confirm** (operator action) into Product Truth — never auto-write from the adapter.
- **Persist** confirmed facts + analysis reference provenance (not raw payload as authority).
- **Readiness** may check integration contract existence, supported version, structural validity, source hash, provenance completeness, and that observations remain unconfirmed until operator action — **not** geometric correctness of the external parse.

---

## 4. Forbidden WorkOS responsibilities

Do not implement or extend:

- SVG / DWG / DXF / CAD parsers
- Geometry extraction; path / polygon / text / font / group / layer detection
- Nesting; auto-grouping; automatic component binding
- File preview intelligence; artwork teaching engines; ML grouping
- Geometric inference; visual recognition; file-to-Product-Truth conversion

Do not create services named (examples): `SvgAnalyzer`, `DwgAnalyzer`, `DxfParser`, `ArtworkIntelligenceService`, `ShapeDetectionService`, `AutoGroupingService`, `ArtworkUnderstandingEngine`, `GeometryInferenceService`, `FileToComponentMapper`.

Existing in-repo analysis code: **do not extend**. Classify as LEGACY / EXPERIMENTAL / DEFERRED / EXTERNAL_APP_OWNED. **Do not delete without owner GO.**

---

## 5. Authority transition

| Stage | Status label | Authority |
|-------|--------------|-----------|
| Desktop emits entities / measurements / observations | `observed` | Observation only |
| Desktop or WorkOS surfaces suggested bindings | `proposed` | Suggestion only — **never** confirmed |
| Operator accepts into Product Truth | `confirmed` | Sole commercial/execution authority |

Suggested bindings **always start as `proposed`**. The consume adapter must reject or coerce any inbound binding marked `confirmed`.

---

## 6. Provenance (minimum)

External payload and Product Truth confirmation must carry or reference:

| Field | Purpose |
|-------|---------|
| `analysis_id` | Stable id for this analysis run |
| `analysis_version` | Desktop app analysis build/version string |
| `artwork_analysis_contract_version` | Contract schema version (e.g. `artwork_analysis_contract_v1`) |
| `source_file_name` / `source_file_hash` / `source_file_kind` | Source identity |
| `source_entity_ids` | Ids of entities confirmed from |
| Optional: producer app name/version, produced_at | Audit trail |

Product Truth stores **confirmed facts + analysis reference provenance**. It does not treat the full raw external payload as authority.

---

## 7. Minimal contract pointer

Runtime consume-only types:

- Backend: `backend/schemas/artwork_analysis_contract_v1.py`
- Adapter: `backend/services/artwork_analysis_intake_adapter.py`
- Frontend review contract: `frontend/src/lib/artworkAnalysis/artworkAnalysisContractV1.ts`
- UI stub: `frontend/src/features/product-system/ArtworkAnalysisReviewPanel.tsx`

Transport: **TBD**.

---

## 8. Relation to operator teaching model

[`2026-07-20_ARTWORK_UNDERSTANDING_OPERATOR_TEACHING_MODEL.md`](./2026-07-20_ARTWORK_UNDERSTANDING_OPERATOR_TEACHING_MODEL.md) remains valid for observation vs interpretation vs confirmation **semantics**.

**Ownership update:** deterministic observation/parse of graphic files is owned by the **desktop analysis app**, not by new WorkOS parsers. WorkOS validates consumed external observations and never invents groups or writes Product Truth without operator confirmation.

Build 2 internal teaching/grouping engines remain deferred / out of WorkOS implementation scope under this boundary.

---

## 9. Inventory policy for existing code

| Classification | Meaning |
|----------------|---------|
| **ACTIVE (legacy runtime)** | Still imported by Intake V6 / related paths — treat as transitional consumer of file analysis inside WorkOS; do not extend analysis capability |
| **LEGACY** | Older parallel analyzers; keep until GO |
| **EXPERIMENTAL** | Proof/QA-only |
| **DEFERRED** | Planned WorkOS analysis work cancelled by this boundary |
| **EXTERNAL_APP_OWNED** | Responsibility moved to desktop; WorkOS keeps integration surface only |
| **UI-ONLY** | Display of analysis results without new parse logic |

See living inventory in the Product System authoring worklog continuation (2026-07-20 External Artwork Analysis Boundary).
