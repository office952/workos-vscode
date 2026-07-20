# External Artwork Analysis Boundary — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `db64b4646625220c05a06b8e789880e91e494ef2` |
| Owner GO | Boundary + Product System continuation |
| Verdict | **PASS_WITH_WARNINGS** (boundary locked; transport TBD; legacy analyzers still present — not extended) |

---

## 1. Scope

Document permanent ownership of graphic-file intelligence outside WorkOS; ship minimal consume-only contract + adapter + readiness checks + review UI stub; continue Product System within prior accepted model. Not a new audit; not architecture reopen of prior completion gates.

## 2. Kickoff confirmation

| Item | Result |
|------|--------|
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `db64b46` reconfirmed |
| Dirty tree | ~360+ preserved |
| Prior gates | Preserved (not re-proven) |

## 3. Product System build state (preserved)

| Axis | Status |
|------|--------|
| Build | PASS_WITH_WARNINGS |
| Runtime | PASS_WITH_WARNINGS |
| UI | NEEDS_POLISH |
| Figma | PROPOSED |
| Template publication | BLOCKED (aluminiu inactive) |
| Direction (prior) | ~92 |

## 4. Absolute limit

STOP all new/extended WorkOS SVG/DWG/DXF (and other graphic) analysis. Desktop app owns file intelligence. WorkOS owns product/business/execution truth + integration contracts.

## 5. Canonical flow

Desktop Analysis App → external structured result (observed/proposed) → WorkOS Intake/Product System → Operator review → Confirm → Product Truth → PD/Agg/Qty/CPP/EIC/Snapshot/Order/Execution.

## 6. Documentation delivered

| Doc | Role |
|-----|------|
| `docs/architecture/artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md` | Canonical ownership |
| Teaching model + AGENTS.md + `WORKOS_SYSTEMS_ALIGNMENT_MAP.md` | Amended pointers |
| Living worklog continuation | Same authoring e2e worklog |

## 7. Contract summary (`artwork_analysis_contract_v1`)

Lean fields: `artwork_analysis_contract_version`, provenance (`analysis_id`, `analysis_version`, source file name/hash/kind, entity ids), entities, groups, measurements, observations, suggested_bindings (status **proposed** only), confidence, extensions. Unknown versions rejected. Transport **TBD**.

## 8. Adapter shape

`consume_external_artwork_analysis` / `validate_artwork_analysis_payload` — validate + review surface; `write_performed=false`; `product_truth_written=false`; optional `analysis_reference_for_product_truth` for confirmed provenance refs only.

## 9. UI review surface

`ArtworkAnalysisReviewPanel` — read-only stub; empty state on Product System Lifecycle tab; no confirm button; no file parse.

## 10. Operator → Product Truth

Adapter never auto-writes. Suggested bindings cannot be inbound `confirmed`. Operator confirmation (existing Product Truth paths) remains sole authority. Qty/PD/Agg consume confirmed truth only. Snapshot freezes confirmed revision + analysis reference/hash — no desktop re-read at freeze.

## 11. Readiness integration

Standalone `evaluate_artwork_analysis_integration_readiness`: supported version, structural validation, provenance, proposed≠confirmed bindings, no PT write, geometry correctness **not claimed**. Wired into product E2E readiness **only when** external bag present; findings non-blocking so prior BUILD/TEMPLATE axes are not reopened.

## 12. Inventory classification table

| Path / area | Classification | Active workstream? | Notes |
|-------------|----------------|--------------------|-------|
| `frontend/src/lib/svgAnalyzer/**` | ACTIVE (legacy) / EXTERNAL_APP_OWNED | No (do not extend) | Intake V6 nest2 consumer |
| `IntakeV6SvgAnalyzerStep` / Review analyzerReport | ACTIVE (legacy UI) | No extend analysis | UI-only consumption of legacy report |
| `backend/services/intake_v3_svg_analysis_service.py` | ACTIVE (legacy) | No | Called from intake_v6_workspace_service |
| `backend/services/svg_analyzer.py` | LEGACY | No | V5 parallel |
| `backend/services/svg_layer_analysis_service.py` | LEGACY | No | |
| `backend/services/svg_path_metrics.py` / `svg_metrics_service.py` | LEGACY / support | No | Metrics helpers |
| `backend/services/svg_preview_service.py` / `svg_sanitization_service.py` | UI-support / LEGACY | No | Not intelligence authority |
| `backend/services/svg_component_binding_*` | LEGACY binding path | No extend auto-bind | Operator/confirm paths separate |
| `backend/services/acm_dxf_path_measurement.py` | LEGACY / EXPERIMENTAL | No | ezdxf; AcmPanel QA |
| `backend/services/acm_production_geometry_attachment.py` | LEGACY / EXPERIMENTAL | No | dxf_parse warnings |
| `ezdxf` in requirements-dev | LEGACY dep | No delete without GO | Dev/test AcmPanel |
| `fisiere-teste-svg/**` | Fixtures | N/A | Test assets |
| New `artwork_analysis_contract_v1` + adapter + readiness | ACTIVE (integration) | Yes — consume only | This task |
| Artwork teaching / Build 2 engines | DEFERRED | No | Boundary forbids WorkOS implementation |

## 13. No current workstream implements new analysis

Confirmed: this continuation adds consume/review/readiness only. No new parser services. Legacy analyzers classified, not extended, not deleted.

## 14. Forbidden confirmation

| Forbidden | Status |
|-----------|--------|
| SVG/DWG/DXF parser/analyzer | Not implemented/extended |
| Auto-grouping / geometric inference | Not implemented |
| AI as Product Truth authority | Not implemented |
| Direct PT write from adapter | Tested false |
| Aluminiu activation | Not done |

## 15. Tests run

```text
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_artwork_analysis_contract_v1.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/artworkAnalysis/artworkAnalysisContractV1.test.ts src/features/product-system/ArtworkAnalysisReviewPanel.test.tsx
```

(Results recorded after execution in §24.)

## 16. Commits

| SHA | Group |
|-----|-------|
| `7e2a1a4` | docs: External Artwork Analysis Ownership boundary |
| `66cf0ef` | feat(schemas): artwork_analysis_contract_v1 + adapter validation |
| `99d9442` | feat(ui): external artwork analysis review stub |
| `9da0244` | docs(qa)/worklog + allowlist + report |
| `1864d92` | docs(qa): note boundary tip HEAD (pre-fixup) |

## 17. Stop conditions

| Condition | Hit? |
|-----------|------|
| Major new schema required | No |
| Transport must be decided now | No (TBD documented) |
| Payload can't version | No |
| Product Truth can't hold provenance | No (reference helper) |
| Qty needs raw geometry | No |
| Critical runtime depends on inseparable internal parser | Partial legacy dependency remains — classified, not deleted |
| Deleting SVG/DWG dep would break runtime | Not attempted |

## 18. Non-scope respected

No parsing/rendering/CAD/OCR/CV/auto-group/AI/desktop app/desktop transport/PI/CI/Build2/Aluminiu/pricing/EP materialization/mobile.

## 19. Direction score split

| Axis | Score |
|------|-------|
| Product System | 90 |
| External boundary | 95 |
| UI | 78 |
| Runtime integration readiness | 72 |

## 20. Overall direction (continuation)

**~84/100** for this boundary slice; prior completion ~92 preserved and not reopened.

## 21. Risks / warnings

- Legacy in-repo analyzers still execute on Intake V6 paths until migration GO.  
- Transport TBD — no live desktop sync.  
- ezdxf remains in requirements-dev for AcmPanel QA.  

## 22. Next recommended (owner GO)

1. Decide transport (HTTP/file/folder/sync).  
2. Migration plan: Intake V6 stops calling in-repo analyze; consumes external bag.  
3. Separate GO for legacy analyzer deprecation/deletion.  

## 23. PAREREA MEA SINCERA

Boundary-ul e clar și necesar — fără el, Build 2 / teaching / svgAnalyzer ar fi continuat să crească în WorkOS. Contractul v1 e suficient de slab ca să nu blocheze desktopul, dar destul de strict pe version + proposed≠confirmed. Warning-ul real: runtime-ul încă rulează analiză internă; documentarea fără migrare lasă dublă realitate. Nu am șters nimic — corect. Transport TBD e onest; fără el, readiness „integration” rămâne parțial.

## 24. Commands + results

```text
pytest tests/test_artwork_analysis_contract_v1.py -q
→ 7 passed

vitest run artworkAnalysisContractV1.test.ts ArtworkAnalysisReviewPanel.test.tsx
→ 4 passed (2 files)
```

## 25. Return envelope (parent)

| Field | Value |
|-------|--------|
| Verdict | PASS_WITH_WARNINGS |
| Kickoff HEAD | `db64b46` |
| Tip HEAD | `1864d92` |
| Commit SHAs | `7e2a1a4`, `66cf0ef`, `99d9442`, `9da0244`, `1864d92` |
| Doc paths | ownership + worklog + this report + allowlist |
| Inventory | §12 |
| Stop conditions | None hard-stop; transport TBD |
| Direction scores | §19 |
