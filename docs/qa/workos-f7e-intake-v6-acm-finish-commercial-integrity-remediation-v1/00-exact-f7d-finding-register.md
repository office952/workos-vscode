# F7E Stage A — Exact F7D Finding Register

Scope: read-only reconciliation of `workos-f7d-intake-v6-acm-commercial-integrity-audit-v1` (Agent A + Agent B raw findings + Lead report). No code touched. Source files read in full:

- `agent-a-findings-summary.json` (13 findings, F1–F13)
- `agent-b-findings.json` (9 findings, AGENT-B-F001–F009)
- `WORKOS_F7D_INTAKE_V6_ACM_COMMERCIAL_INTEGRITY_AUDIT_V1_REPORT.md` (Lead verdict)
- `agent-b-commercial-delta-matrix.md`, `agent-b-finish-results.md`

## 0. Count reconciliation (why this register exists)

The three F7D sources disagree slightly on totals. This register resolves that by using the **raw per-finding `severity`/`priority` field** in each agent's own JSON as ground truth, then applying exactly **one** dedup merge (§2), and reports the delta against each prior summary so nothing is silently "corrected" without a trail.

| Source | P0 | P1 | P2 | P3 | Total | Note |
|---|---|---|---|---|---|---|
| Agent A `findings-summary.json` (raw) | 2 | 2 | 5 | 4 | 13 | F1,F4 / F2,F3 / F5–F9 / F10–F13 |
| Agent B `findings.json` (raw, counted from per-finding `severity` field) | 2 | 3 | 2 | 2 | 9 | F001,F002 / F003–F005 / F006,F007 / F008,F009 |
| Agent B `return_to_lead` self-reported block (same file, bottom) | 2 | 3 | **3** | 2 | **10** | Internally inconsistent with its own 9 findings above — off by one on P2. Not usable as-is. |
| Lead `WORKOS_F7D_..._REPORT.md` verdict block | **4** | **5 (approx.)** | **6+** | **4+** | ~19+ | Explicitly hedged ("approx.", "6+", "4+") — not exact. |
| **This register (raw sum, both agents, no dedup)** | 4 | 5 | 7 | 6 | 22 | 2+2 / 2+3 / 5+2 / 4+2 |
| **This register (exact, after the one dedup merge in §2)** | **4** | **4** | **7** | **6** | **21** | Ground truth for F7E Stage B/C planning |

Reconciliation notes:
- Agent B's own bottom-of-file `return_to_lead.p2_count: 3` does not match the 2 findings actually tagged `"severity": "P2"` (AGENT-B-F006, AGENT-B-F007) in the same document. Treated as a stale/manual miscount in the source; **2** is used.
- The Lead report's P1 "5 (approx.)" is explained by §2: it is the raw A+B P1 sum (2+3=5) *before* moving AGENT-B-F005 into the merged P0 cluster. After the merge, exact P1 = **4**.
- The Lead report's P0=4 verdict is already the **post-dedup** number and matches this register exactly.
- P2 (7) and P3 (6) below are **reference counts only** per the task brief — no P2/P3 dedup was found necessary (no A↔B overlap in those tiers).

## 1. Exact totals (use these)

```text
P0 = 4   (exact, deduplicated)
P1 = 4   (exact, deduplicated)
P2 = 7   (reference — no cross-agent overlap found)
P3 = 6   (reference — 4 are UX/hygiene items, 2 are Agent B "confirmed correct behavior" controls, not defects)
Total unique findings = 21
```

## 2. The one A↔B dedup merge

| Merged ID | Sources | Why merged |
|---|---|---|
| **F1/B-F005** | Agent A `F1` (P0) + Agent B `AGENT-B-F005` (P1 as authored) | Both describe the *same* workspace state at Step 1 "Straturi": the ACM/Alucobond layer is simultaneously shown as "Selectat/Inclus în propunere" (composition card) **and** flagged "standby, nu intră în quote" (footer warning), while the payload's `status` field and Step 2 pricing rail disagree again. Agent A traced 3–4 contradictory surfaces; Agent B traced 2 of the same surfaces independently. One symptom, one root-cause family (§3). Consolidated severity = **P0** (Agent A's tier governs — it is the more complete trace and the Lead report already promotes it to P0 in the verdict block). |

No other findings overlap. All other A and B findings describe distinct symptoms even where they touch the same file (e.g. A-F5 raw-diagnostic-code leakage vs B-F004 schema-vocabulary divergence both touch finish contracts but are different defects).

## 3. Symptom → shared root cause map

| Root cause | Findings that share it |
|---|---|
| `backend/data/commercial_rules_volumetric_v2.py` line `finisaje_colantare_vopsire` (`VOL_V2_FINISH_M2_OR_MINIMUM`, lines 142–156) — single flat rate, no `material_gate_path`, fires for every face/cant selection incl. "none" | AGENT-B-F001 (P0), AGENT-B-F006 (P2, Oracal/RAL cant), AGENT-B-F007 (P2, confirmation-state warning theater — same rule, same lack of gating) |
| Architectural split: EIC informational cost services (`intake_v4_oracal_face_pricing_service.py`, `intake_v4_ral_paint_rules_service.py`) never consulted by CPP | AGENT-B-F002 (P0) — root of AGENT-B-F001's *margin* framing |
| ACM standalone-template geometry validator built for letter-shaped fields (`CRITICAL_GEOMETRY_MISSING`) rejects valid ACM-only payloads before any finish rule runs | AGENT-B-F003 (P1) — isolated, no other finding shares this root |
| `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.ts:501` (unconditional "standby" warning for `support_panel`/`bond_panel` roles) vs `frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx:314` ("Inclus în propunere" chip) — two independent surfaces reading different state with no single source of truth | F1/B-F005 (P0, merged) |
| `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts` — the Step-3 recap view-model (`IntakeV6ConfirmSummaryViewModel`) has **zero** ACM/support-panel fields; `IntakeV6ConfirmDashboard.tsx`'s `buildFinishSummaryLine()` only reads `letterRows`/`artworkRows`/`vinylFace`/`lighting`/`backingForex` | A-F4 (P0) |
| Same Step-1 composition-card single "Confirmă" control area | A-F2 (P1, bundles mandatory+optional confirm) — thematically adjacent to F1/B-F005 but a distinct control-design defect, kept separate |
| `backend/schemas/intake_v4.py` finish-type fields typed `str \| None` with no `Literal`/enum | AGENT-B-F004 (P1) — isolated |
| Operator-facing copy hygiene (raw internal strings rendered verbatim) | A-F3 (P1, ownership doc text in ACM "Avansat" section), A-F5 (P2, `canonical_unresolved_warning:*` codes + raw JSON dump) — same theme, different exact surfaces, kept separate |
| Step-2 tab layout duplication | A-F6 (P2, transformer/PSU decision on 2 entry points), A-F7 (P2, 4× repeated commercial-adjustment widgets) |
| Positive controls proving the CPP mechanism itself is sound | AGENT-B-F008 (P3, stock cant colors zero-delta is correct-by-design), AGENT-B-F009 (P3, `sablon_montaj` paper/Forex +10 RON delta proves `material_gate_path` works) — **not defects**, cited as root-cause evidence for AGENT-B-F001 |

## 4. Full register

| ID | Severity | Scenario | Expected | Actual | Root owner | Impl. group |
|---|---|---|---|---|---|---|
| **AGENT-B-F001** | P0 | Switch face Oracal series (641/651/8500) or cant to Oracal-wrap/RAL, geometry held constant | Total should move — internal material spread is >3× (6.5→20 EUR/m²) and RAL has an owner-documented 100 RON/color minimum | Total identical (577.50 RON API / 2.288,75 RON live) across all 13 face+cant variants tested | `backend/data/commercial_rules_volumetric_v2.py:142-156` (`finisaje_colantare_vopsire`) | G1 — commercial rule authoring |
| **AGENT-B-F002** | P0 | Compare EIC material rates (`intake_v4_oracal_face_pricing_service.py`) to the CPP finish line | Customer price should not be provably insensitive to a >3× internal cost spread | EIC differentiation exists, is `informational_only`, never read by `CommercialPriceProposalService` | No bridge between EIC and CPP; `backend/data/commercial_rules_volumetric_v2.py` | G1 — commercial rule authoring |
| **F1/B-F005** (merged) | P0 | Open Step 1 "Straturi" for a workspace with an ACM/Alucobond layer | One consistent inclusion status shown everywhere it's referenced | 3–4 contradictory statements: footer "standby, nu intră în quote", composition chip "Inclus în propunere", payload `status=available_optional` w/ `applied_content=[letters]` only, Step 2 rail prices 6 ACM lines (86,77 EUR) into the visible total, Step 3 recap omits it | `intakeV4QuoteGeometry.ts:501` + `IntakeV6ProductCompositionPanel.tsx:314` + payload status sync | G2 — ACM inclusion honesty (frontend) |
| **A-F4** | P0 | Reach Step 3 "Recapitulare" with an ACM panel already priced into the visible total | Recap should list every product/component that contributed to the total the operator is about to price into an offer | Recap only lists letters (geometry/finish/LED); ACM panel — already 86,77 EUR of the total — is absent | `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts` (no ACM field) | G2 — ACM inclusion honesty (frontend) |
| **A-F2** | P1 | Click "Confirmă" on the Compoziție produs card with both mandatory letters + optional ACM panel present | A distinct yes/no decision point for the optional component | Single click confirms both mandatory and optional components together | `IntakeV6ProductCompositionPanel.tsx` (Step 1 composition card) | G2 — ACM inclusion honesty (frontend) |
| **A-F3** | P1 | Open ACM tab → "Avansat" section | Operator-facing copy only | Raw internal ownership-doc string rendered verbatim: "Ownership: MOUNTING → structura_suport + sablon_montaj · …" | Step 2 ACM tab "Avansat" render path | G5 — UX/copy hygiene |
| **AGENT-B-F003** | P1 | `POST /commercial-price-preview/TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` with valid ACM-only fields (`panel_width_mm`, `panel_height_mm`, `acm_thickness_mm`, `return_depth_mm`, `fold_sides`) | Structurally valid ACM payload reaches commercial rule evaluation | All 4 shell-finish variants return `status=blocked`, `CRITICAL_GEOMETRY_MISSING`, fixed `commercial_total=34.0`, identical regardless of finish | `backend/services/commercial_price_proposal_service.py` geometry validator (letter-shaped field expectations) + `acm_quote_input_helpers.py` | G3 — ACM geometry validator |
| **AGENT-B-F004** | P1 | Submit `return_finish_type="mirror_silver"` (not offered by the live UI combobox) to CPP preview | Validation error/warning, or documented confirmation the wider vocabulary is intentional | Silently accepted, `status=ready`, no warning; separately UI emits short tokens (`white`/`black`) while schema/canonical map use suffixed tokens (`white_aluminum`) with no normalization bridge found | `backend/schemas/intake_v4.py:102-105,137-141,196-200` (`str \| None`, no `Literal`) | G4 — finish contract vocabulary |
| **A-F5** | P2 | Any workspace with unresolved warnings; open ACM "Detalii tehnice" | Operator-facing copy only | `canonical_unresolved_warning:*` codes (e.g. `PROCESS_MAP_DEFAULT_ILLUMINATED_TRUE_TEMPLATE_ONLY`) and a raw pretty-printed JSON component dump shown directly to operator | Shared warnings footer + ACM "Detalii tehnice" collapsible | G5 — UX/copy hygiene |
| **A-F6** | P2 | Open ACM tab "Avansat" and "Alimentare și service" sub-block on same Panou/carcasă tab | One decision point per decision | Transformer/PSU service-corner selection appears twice as separate controls | Step 2 Panou/carcasă tab layout | G5 — UX/copy hygiene |
| **A-F7** | P2 | Open all 4 Step-2 Configurare tabs | Global commercial-adjustment widgets (Adaos/Discount/TVA/Ajustare) live once | Identical 4-widget block repeated as tab-body content on every tab | Step 2 tab shell composition | G5 — UX/copy hygiene |
| **AGENT-B-F006** | P2 | Compare `canonicalFinishEnumMap.ts` cant-Oracal/RAL entries to `commercial_rules_volumetric_v2.py` | N/A — reclassifies F001's cant rows from "unknown gap" to "known/anticipated missing rule" | No rule references `MAT-ORACAL-641/651`, `MAT-VOPSEA-RAL-CANT-*`, `RETURN_CANT_VINYL_APPLICATION_LABOR`, `RETURN_CANT_RAL_PAINT_LABOR`, or the 100 RON RAL minimum, despite owner-confirmed ownership | `backend/data/commercial_rules_volumetric_v2.py` vs `frontend/src/features/product-system/canonicalFinishEnumMap.ts` | G1 — commercial rule authoring |
| **AGENT-B-F007** | P2 | Submit `letter_group_finishes[].confirmed = true/false/[]/None`, all else constant | Unconfirmed/empty/absent state should differ from confirmed (block, `owner_decision_required=true`, or different total) | All 4 states → `status="ready"`, `commercial_total=577.50` identical; only warning text changes | `backend/services/commercial_price_proposal_service.py` (warning generation decoupled from gating) | G1 — commercial rule authoring |
| **A-F8** | P2 | Open ACM tab, view "Cadru interior" checkbox | Checkbox state should not contradict adjacent caption | Checked+readonly next to "Nicio relație de montaj confirmată" (no mounting relation confirmed) | ACM tab render/PD binding | G2 — ACM inclusion honesty (frontend) |
| **A-F9** | P2 | Pick wrong "Ce producem?" scope mode, then try to change it after layer confirmation starts | Visible in-workspace path to change scope | Selector becomes disabled mid-flow; no path without restart | Step 1 scope-mode state machine | G5 — UX/copy hygiene |
| **A-F10** | P3 | View ACM panel "Lățime (mm)" field | Clean integer/rounded mm value | Shows `2000.001` (SVG-to-mm float artifact) | SVG geometry conversion → form field | G5 — UX/copy hygiene |
| **A-F11** | P3 | Open "Module produs" combobox (Volum aluminiu modular) | Static text if no real choice exists | Single-option combobox presented as an interactive choice | ACM tab render | G5 — UX/copy hygiene |
| **A-F12** | P3 | Inspect `litere-cu-fundal-acm-segmentat*.svg`, `LITERE-VOLUMETRICE-ACP.svg` | Filename matches content | Filenames reference ACM/ACP but contain no Alucobond/support-panel geometry | Fixture repo hygiene | Reference only — no build |
| **A-F13** | P3 | Note: `pbl-complex.svg` (ACM background + 2 letter groups + logo + cutout text) not exercised this session | Follow-up coverage | Time-boxed out; flagged as top follow-up fixture | Coverage gap, not a defect | Reference only — no build |
| **AGENT-B-F008** | P3 (not a defect) | Switch `return_finish_type` among white/black/gold/silver | Zero delta per owner design (no tariff for stock colors) | Zero delta confirmed — matches design | `canonicalFinishEnumMap.ts:cant_stock_color` | Reference — proves correct behavior |
| **AGENT-B-F009** | P3 (not a defect) | Switch `mounting_template_material_type` paper↔forex | Distinct rule rows should produce a delta | +10.00 RON delta confirmed — mechanism works | `commercial_rules_volumetric_v2.py:170-204` | Reference — positive control for G1 |

## 5. Implementation groups referenced above (defined fully in `02-architecture-proposal.md`)

- **G1** — Commercial rule authoring (`backend/data/commercial_rules_volumetric_v2.py`, `commercial_price_proposal_service.py`)
- **G2** — ACM inclusion honesty (frontend Step 1/2/3: `intakeV4QuoteGeometry.ts`, `IntakeV6ProductCompositionPanel.tsx`, `intakeV6ConfirmSummary.ts`, `IntakeV6ConfirmDashboard.tsx`)
- **G3** — ACM standalone-template geometry validator (`commercial_price_proposal_service.py`, `acm_quote_input_helpers.py`)
- **G4** — Finish contract vocabulary (`backend/schemas/intake_v4.py`, `canonicalFinishEnumMap.ts` token alignment)
- **G5** — UX/copy hygiene and duplication cleanup (non-blocking, can run independently of G1–G4)
