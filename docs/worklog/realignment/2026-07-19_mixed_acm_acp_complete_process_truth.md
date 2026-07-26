# 2026-07-19 — Mixed ACM/ACP complete process truth consolidation

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD initial | `849c776` |
| Scope | Docs-only complete consolidation (finish, segmented, electrical, atelier/montaj) |
| GO | Research / docs / Semgrep local / gh read-only — **no** product code |

## Deliverable (canonical — single principal)

`docs/architecture/MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` — extended in place (not a second principal doc).

Prior baseline audit worklog: `2026-07-19_mixed_acm_acp_technical_truth_audit.md`.

## Parallel tracks (subagents)

| Track | Agent | Focus | Confidence |
|-------|-------|-------|------------|
| Finish / Oracal / print | [Finish track](22493a49-c16e-4702-957c-81d0af5d70e6) | face≠return; Oracal widths; print+lam ops; face+first-fold gap | High |
| Letters LED/Forex order | [Letters order](85efa906-5df1-499e-abb8-fa7023518fee) | dossier + graph; LED before attach; soft vs hard graph | High |
| SVG segmented | [SVG track](bff3234a-b2ec-44ea-965e-6b87c73443a4) | Desktop SVG examples; 1 SUPPORT_CONTOUR limit | High |

Principal agent reconciled into one coherent SoT.

## Sources

### Mandatory architecture
- `03_PRODUCT_DEFINITION_COMPILER.md`, `05_PRODUCT_AGGREGATE_FLOW.md`, `08_EXECUTION_PLAN_FLOW.md`, `10_EXECUTION_PLAN_TASK_GRAPH.md`
- `14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md`, `18_GOVERNANCE_SETTINGS_POLICY.md`, `21_WORKOS_IMPLEMENTATION_ROUTE.md` (boundary awareness)
- Prior canonical: `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` @ `849c776`

### Letters (order not invented)
- `LITERE_VOLUMETRICE_LUMINOASE_CANONICAL_PRODUCT_DOSSIER.md`
- `LITERE_VOLUMETRICE_LUMINOASE_PROCESS_DEPENDENCY_GRAPH.md`
- Confirmed: LED pe Forex înainte de prinderea spatelui; ATTACH_BODY după TEST_LED_ON

### Terminology / shell / finish
- `ACP_ACM_DIBOND_TERMINOLOGY_MAP.md`, `ACP_INTERNAL_FRAME_OWNER_RULES.md`
- Face treatment / local module docs
- Oracal: `MAT-ORACAL-651` / usable widths ~960/1220 in catalog path
- Live: `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`, `TPL-VOLUMETRIC-LETTERS_v2`
- Legacy: `TPL-ACP-LIGHT-ROUTED` = PARALLEL_LEGACY_COST_PATH; `TPL-BOND-CASETAT` dead

### SVG examples (Desktop — not repo SoT)
- `litere-cu-fundal-acm-segmentat.svg`
- `litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg`
- `situatie-3.svg`

## GitHub / Semgrep

| Tool | Use |
|------|-----|
| `gh` | auth status only this pass; **zero write** |
| Semgrep 1.170.0 | `--metrics=off`; scoped pattern scans on `backend/data` / `backend` for Bond + `sablon_montaj`; no autofix; no cloud |
| rg | Oracal, SUPPORT_CONTOUR MAX_ONE, face/return finish |

## Owner truth consolidated (new since `849c776`)

1. Finisaj față ≠ volum; Oracal vs print+laminare distinct.  
2. Strategii colantare: față+primul pliu → față+volum separat → îmbinări + mesaj client calm.  
3. Fundal segmentat: propunere confirmare; nu împărțire automată; panouri ≠ produse independente.  
4. Compoziție distribuită = normală.  
5. Literă aplicată peste îmbinare = executabil, montaj 2 etape („temporar nesprijinită”).  
6. Decupaj / insert 10 mm peste îmbinare = blocker.  
7. Șablon unic owner = Litere (forme pline vs ghidaje/crop).  
8. 220V + trasee per panou; atelier vs montaj separate; fără taskuri electrice duplicate.  
9. Ordine LED/Forex din dossier/graph — nu presupusă.

## Contradictions kept explicit

1. Graph soft-parallel ATTACH vs owner LED-before-ATTACH → docs prefer owner + dossier.  
2. Multi-panel assembly MISSING runtime (max 1 SUPPORT_CONTOUR).  
3. Finish Contract shell (față+primul pliu) MISSING runtime.  
4. Frame profile SKU still DEFERRED.  
5. CNC/Oracal-after-fixing task_rules incomplete.

## Files touched (docs only this commit)

- `docs/architecture/MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md`
- `docs/architecture/ACP_ACM_DIBOND_TERMINOLOGY_MAP.md`
- `docs/architecture/ACP_ACRYLIC_INSERT_LOCAL_MODULE.md` (§ pointer)
- `docs/architecture/ACP_ROUTED_BACKLIT_LOCAL_MODULE.md` (§ pointer)
- this worklog

## WIP foreign — untouched

Backend/frontend/test/screenshot WIP and other untracked trees left as-is. Exact-path staging only.

## Validations

- Repo search + terminology + Oracal + segmented + letters order + SVG path existence
- Semgrep local scoped
- No product code in staged set
- No full regression (docs-only)

## Commit

Planned: `docs(product-system): complete mixed ACM ACP process truth`

## Follow-up

Segmented assembly + joint rules contract foundation shipped after this docs commit — see  
`2026-07-19_segmented_acm_acp_background_contract_foundation.md`.  
Șablon ACM/ACP vinyl truth closed there (no longer open paper vs Forex for that context).
