# INTAKE_V6_SVG_TRUTH_CONTRACT_REPAIR_V1

**Status:** Implemented — forward-fix only  
**Data:** 2026-07-20  
**Evidence:** `docs/audits/_evidence/2026-07-20_intake-v6-svg-truth-repair/`  
**Owner gate remaining:** historic remediation + UI system audit resume

---

## 1. Rezumat executiv

Reparatie E2E pentru P1–P3/P7 pe lanțul SVG → Product Truth → persistence → reinspection. Fără redesign UI, fără 21st, fără remediation automată pe date istorice.

Runtime pe fixtures Desktop: **PASS** (ACM: `PROPOSED` + 2 panels + provenance + zero phantom artwork + Straturi reopen; gradi: zero support pe logo + 2 artwork rows + Straturi reopen). Golden `gradi-curat`: **PASS**.

## 2. Mini decizia implementată

R1–R5 aprobate: segment ownership, support evidence, logo_presence, Confirm All parity, forward-fix only.

## 3. Contractele finale

| Contract | Valoare |
|----------|---------|
| Support ownership | 1 assembly/component; `panels[]` geometrii component-owned |
| Letters | Componente distincte; neabsorbite de support |
| `support_panel` high | Dovezi cumulative + exclude artwork/logo candidates |
| `logo_presence` | `detected_confirmed` \| `optional_absent` \| `slot_available` |
| Finish rows | Doar când presence permite + rol artwork; hard exclude support/face |
| Confirm All | Același path ca select manual pentru support + segmented PROPOSED |
| Step intent | `operatorStepIntent` supraviețuiește `LOAD_SUCCESS` |

## 4. Fix P1

- Expansion păstrează `sourceGroupIds` + `elementIds` pe layer (ex. `gravare-cnc-135gr`, 2 rects).
- Color cluster rămâne pentru analiză vizuală, nu șterge provenance.
- `buildSupportPanelConfirmationPath` + Confirm All → `segmented_background.status=PROPOSED`, `panels.length=2`.
- Nu `rect = Product Template`.

## 5. Fix P2

- `isArtworkOrLogoCandidateLayer` (origin/id/name/guess) — nu doar regex `logo_instance_*`.
- Refine exclude candidații din `strongSupportIds`; reverse support→printed_artwork pe conflict.
- Confirm All refuză support pe artwork candidates.
- Golden: `{ face:4, printed_artwork:2 }`.

## 6. Fix P3

- Paint: fill+stroke tehnic ≠ policromie.
- `deriveArtworkFinishesFromAnalyzer` consumă `logo_presence`; exclude support/face.
- ACM: 0 artwork rows; gradi: 2 rows pentru logo reale.

## 7. Fix P7

- `operatorStepIntent` pe `SET_STEP`.
- `LOAD_SUCCESS` / finish persist nu bounce de pe Straturi dacă intent=layers.
- Hydrate restabilește chip/preview/rows (runtime proof).

## 8. Files changed

Vezi WORKLOG. Principale: analyzer refine/paint/expansion, `intakeV6LogoPresence`, `intakeV6SupportPanelConfirmationPath`, `IntakeV6SvgAnalyzerStep`, workspace reducer/contracts.

## 9. Tests

| Suite | Result |
|-------|--------|
| `goldenSvgFacts.test.ts` | PASS |
| `intakeV6LogoPresence.test.ts` | PASS |
| `intakeV6SupportPanelConfirmationPath.test.ts` | PASS |
| `intakeV6WorkspaceReducer.p7.test.ts` | PASS |
| `ana-maria-layer-roles.test.ts` | PASS |
| `guessLayerAutoRole.supportProposal.test.ts` | PASS |
| Runtime both SVG | PASS |

## 10. Runtime proof

| Fixture | Workspace | Key results |
|---------|-----------|-------------|
| ACM | `IV6-379CEB03` | segmented PROPOSED, 2 panels, provenance gravare-cnc-135gr, artwork=0, reopen/refresh layers OK |
| gradi | `IV6-B6C01680` | no support_panel, artwork=2, 6 layers reopen/refresh OK |

Screenshots: `.../acm/*.png`, `.../gradi/*.png`.

## 11. Screenshot-uri UI (P7)

- `05-reopen-layers.png`, `06-after-refresh-layers.png` pentru ambele cazuri.

## 12. Payload before/after

| | Before (audit WS) | After (repair WS) |
|--|-------------------|-------------------|
| ACM segmented | null | PROPOSED, 2 panels |
| ACM artwork | phantom rows possible | 0 |
| ACM provenance | absent | sourceGroupIds + elementIds |
| gradi logo roles | support_panel | printed_artwork |
| gradi Alucobond | false positive | absent |

## 13. Pricing before/after

| | Before | After |
|--|--------|-------|
| ACM | print/laminate pe support posibil | zero artwork finishes pe support |
| gradi | cost ACM inventat | fără support_panel → fără panou fals |

## 14. Remediation dry-run

`dry-run-remediation.json`:

- Scanned known audit WS: 2  
- Suspect: **2** (`IV6-87B98425`: P1+P3; `IV6-3A52D29C`: P2+P1+P3)  
- **Zero writes**  
- Offer/Order downstream: unknown (needs owner-gated SQL expand)

## 15. Dead pieces check

- Shared `buildSupportPanelConfirmationPath` replaces duplicated Confirm All / manual branches for segmented write.
- Artwork finish no longer dual-paths via false policromie.
- Stale expectation `logo-stanga`/`logo-dreapta` in one test updated to `logo_instance_*` (canonical neutral ids).
- No new parallel truth store; payload + client hydrate remain; step intent closes authority gap.

## 16. Riscuri rămase

- Historic workspaces still wrong until remediation GO.
- `slot_available` UI affordance empty not yet surfaced as dedicated empty CTA (by design — no phantom row).
- Full DB suspect inventory not scanned (only known audit IDs).

## 17. Commit

Single isolated commit for this build (message in git log).

## 18. Opinie sinceră

Fix-ul atacă cauza contractuală (identity / refine / finish / step authority), nu UI. Runtime pe fixtures e convingător. Fără remediation pe date vechi, operatorii vor mai vedea workspace-uri „otrăvite” până la GO separat — corect că nu le-am rescris orb.

## 19. Roadmap awareness

1. Owner remediation GO (SQL inventar + tool)  
2. Soak pe truth  
3. Reluare UI system audit / absorbție funcțională — **nu** 21st polish acum

## 20. Direcție stabilită

**84/100** — truth-before-UI respectat; rămâne remediation + disciplina soak.

**PASS gate:** îndeplinit pe checklista din brief (golden verde, gradi fără support, ACM panels, zero phantom Vector Logo pe ACM, Confirm All segmented, Straturi reopen, runtime+screenshots, fără date istorice modificate).

**STOP — așteaptă owner pentru remediation și reluarea UI system audit.**
