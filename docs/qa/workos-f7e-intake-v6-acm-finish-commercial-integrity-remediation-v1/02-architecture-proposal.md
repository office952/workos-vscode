# F7E Stage A — Architecture Proposal (Owner-Required Readback)

Read-only. No production code touched. This document exists so the Owner can read back, in one place, exactly what is owned by what, where the boundary sits, and the smallest contract that would close the P0/P1 findings in `00-exact-f7d-finding-register.md` without violating any protected area in `AGENTS.md`.

---

## 1. Canonical input path (where a finish selection enters the system)

```
Operator UI (Step 2 Configurare tabs)
  → frontend finish_setup.* fields (face_finish_type, face_oracal_code,
     return_finish_type, return_oracal_code, letter_group_finishes[], applied_content, ...)
  → POST /api/v1/product-system/commercial-price-preview/{template_code}
     (backend/routers/commercial_price_proposal.py)
  → CommercialPriceProposalService.build_preview()
     (backend/services/commercial_price_proposal_service.py)
     - reads quote_input / payload dict directly (no ORM finish model)
     - resolves CommercialRuleDefinition rows for the template
       (backend/data/commercial_rules_volumetric_v2.py)
     - resolves quantities via quantity_paths against the same payload dict
     - resolves rates via documented_unit_price OR registry_pricing_code
       lookup (_load_registry_operation_rate → Pricing Registry)
  → CommercialPriceProposalPreview (schemas/commercial_price_proposal.py)
     → rendered in Step 2 right rail ("Ofertă client" total) and Step 3 recap
```

Separately and in parallel, EIC (Estimated Internal Cost) reads the **same raw `finish_setup.*` payload** through a different code path (`intake_v4_oracal_face_pricing_service.py`, `intake_v4_ral_paint_rules_service.py`) to produce internal, `informational_only` cost estimates that never feed the CPP path above. Both sides independently read the same underlying Pricing Registry material rows (`MAT-ORACAL-*`, `MAT-VOPSEA-RAL-CANT-*`) but through separate resolver functions — there is no import from EIC into CPP or vice versa today. **This is correct and must not change** (§5).

---

## 2. Finish ownership (who is allowed to declare a finish exists)

Per `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md` (owner-signed 2026-07-09, HEAD `0a4a346`) and its runtime contract mirror `frontend/src/features/product-system/canonicalFinishEnumMap.ts`:

| Owner | Owns | Truth path prefix |
|---|---|---|
| **RETURN-CANT** | Stock cant colors, Oracal cant wrap, RAL cant paint, the 100 RON RAL minimum policy | `product.components.return_cant.*` |
| **FINISH** | Face vinyl (Oracal 641/651/8500 on face), face print/laminate, artwork vinyl/print/laminate | `product.components.finish.face.*`, `product.components.finish.artwork.instances[]` |
| **FACE** | Substrate, material, thickness, cut path, area/perimeter refs (basis only — not finish application) | `product.components.finish.face` substrate fields |

This is a **Product System** (future) ownership contract, not yet runtime-wired. The **live** Intake V6 → CPP path today uses a flatter, pre-Product-System schema (`backend/schemas/intake_v4.py`: `face_finish_type`, `return_finish_type`, etc., all `str | None`, no enum). Both schemas describe the same real-world finish decisions but are not the same code. Any G1/G4 remediation work must decide, and state explicitly, which of the two it is patching — do not silently merge them.

Cant is **permanently excluded** from FINISH (decision D, ACCEPT) — generic paths `finish.oracal_code`/`finish.ral_code`/`finish.stock_color` are retired/deprecated_conceptual. This exclusion already matches how `commercial_rules_volumetric_v2.py` would need to gate cant vs face rules separately (different `material_gate_path`, different `component_code`).

---

## 3. Component ownership (ACM inclusion)

Today, ACM/Alucobond panel inclusion status is declared independently in **at least 4 places** with no single source of truth:

1. `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.ts:501` — hardcoded warning string for any layer with `role === "support_panel" || role === "bond_panel"`: *"standby, nu intră în quote litere volumetrice"*, unconditional, regardless of actual inclusion state.
2. `frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx:314` — composition-card chip renders *"Inclus în propunere"* whenever `status !== "awaiting template"`.
3. The payload's `product_composition_confirmed` field marks the ACM item `status: "available_optional"` while `applied_content` only ever lists `["letters"]`.
4. `commercial_price_proposal_service.py` prices ACM lines into the visible total (`ACM_STRUCTURA_COMMERCIAL_RULES` + `LETTERS_ACM_COMPOSITION_CONNECTION_RULES`, several with `always_include=True`) — i.e. the *pricing* engine treats it as unconditionally in-scope, independent of both UI messages above.
5. `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts` (Step 3 recap view-model) has **zero** ACM fields, so the final pre-offer screen is silent about it regardless of 1–4.

This is F1/B-F005 (P0) + A-F4 (P0) from the finding register. The fix is a **single boolean/state owner**, not a messaging patch in 4 places (§7).

---

## 4. Commercial rule ownership

`backend/data/commercial_rules_volumetric_v2.py` is explicitly self-documented (file docstring) as a **temporary, local, pre-Pricing-Registry rule table** for "Step 7G/7H" — not the eventual "Step 7I" official Pricing Registry activation. It is the sole owner of "what commercial line exists, at what basis, gated on what payload path" for the live Intake V6 → CPP flow. It must never:

- import/consume `workcenter_rate`, `estimated_minutes`, or any `FORBIDDEN_HOURLY_TOKENS` member (already enforced — see `CRITICAL_MODULE_CODES`/`FORBIDDEN_HOURLY_TOKENS` frozensets),
- invent a RON/EUR figure not already owner-confirmed somewhere (registry seed, `documented_unit_price` constant, or `commercialPolicySource: "cpp_owner_policy"` doc),
- read CostEngine or QuoteOrchestrator (confirmed absent today — keep it that way).

`CommercialPriceProposalService` (`commercial_price_proposal_service.py`) is the sole evaluator: it resolves `quantity_paths`, applies `material_gate_path`/`module_gate` filtering (`_material_gate_matches`, lines 368-375), resolves `registry_pricing_code` via `_load_registry_operation_rate`, and applies rule-specific minimum-charge overrides by `pricing_rule_code` string match (lines 591-601). Any new finish branch (G1) is additive rows in the data file + at most one new `pricing_rule_code`-keyed minimum branch (RAL) — no new mechanism required.

---

## 5. EIC boundary — CPP must not read EIC

**Current state (verified by direct read, zero matches):** `commercial_price_proposal_service.py` contains no import of, or reference to, any `intake_v4_*_pricing_service`/`intake_v4_*_rules_service` module. The separation is real today, not aspirational.

**Why AGENT-B-F002 exists despite this correct separation:** the EIC-side services already compute the *correct*, differentiated material costs (Oracal 6.5/9.0/20.0 EUR/m², RAL tube costs) — they are simply marked `informational_only` and nobody wired an equivalent, independently-authored CPP rule to use the **same underlying Pricing Registry rows** (not the EIC service functions themselves).

**Proposed boundary rule going forward (non-negotiable for G1):**
> New CPP finish rules MUST read rates from the Pricing Registry (`MAT-ORACAL-*`, `MAT-VOPSEA-RAL-CANT-*`, `RETURN_CANT_VINYL_APPLICATION_LABOR`, `RETURN_CANT_RAL_PAINT_LABOR`) via the **same `registry_pricing_code`/`_load_registry_operation_rate` mechanism already used for `logo_print`/`logo_laminate`/`logo_application`/`montaj`, or via a `documented_unit_price` constant sourced from the same registry seed values** (the `sablon_montaj_hartie` pattern). They must **never** `import` from `intake_v4_oracal_face_pricing_service.py` or `intake_v4_ral_paint_rules_service.py`. Those EIC modules stay informational-only and CPP stays a fully independent second reader of the same registry — this is what keeps the EIC/CPP boundary real instead of merging two systems that happen to use the word "finish."

---

## 6. Snapshot boundary

Not directly implicated by any P0/P1 finding in this audit (no G1/G2/G3/G4 branch reads or writes a frozen Quote Snapshot v2 object; CPP is explicitly a **preview** endpoint — `/commercial-price-preview/{template_code}`, no `/price`, no persistence, confirmed by the delta-matrix's own framing: *"read-only preview endpoint... no persistence"*). The one thing to preserve: any new finish rule row must stay inside the existing "read-only preview, no DB write" contract that `commercial_price_proposal_service.py` already declares in its module docstring. If a later build wires CPP output into an actual priced Offer/Snapshot object, that is a **separate, larger boundary decision** outside F7E Stage A/B scope and should get its own Owner gate — flagging it here only so it is not accidentally folded into the G1–G4 remediation.

---

## 7. Confirmed P0/P1 (from `00-exact-f7d-finding-register.md`)

```
P0 (4, exact): AGENT-B-F001, AGENT-B-F002, F1/B-F005 (merged), A-F4
P1 (4, exact): A-F2, A-F3, AGENT-B-F003, AGENT-B-F004
```

---

## 8. Protected paths (per `AGENTS.md` §4 — do not touch without a dedicated build)

None of the G1–G4 work below should require touching: **CostEngine**, **Status lifecycle**, **Snapshots**, **WorkIntake V1**, **QuoteWizard handoff**, or **ProductSystem template registry/activation**. It *will* touch:

- **Pricing** area (`backend/data/commercial_rules_volumetric_v2.py`, `commercial_price_proposal_service.py`) — this is explicitly in-scope for a dedicated remediation build (this is that build's purpose), but every change must stay inside the existing "no hourly basis, no invented rate, read-only preview" contract already enforced in that file.
- No Alembic/schema migration is anticipated — all changes are Python dataclass rows + TS view-model fields, no new DB columns identified in this audit.

---

## 9. Implementation proposal — smallest contract

### G1 — Commercial rule authoring (backend, `commercial_rules_volumetric_v2.py` + service)
1. Add `material_gate_path="finish_setup.return_finish_type"` gated rows for `cant_oracal_wrap` (material: `MAT-ORACAL-641`/`651`, labor: `RETURN_CANT_VINYL_APPLICATION_LABOR`) and `cant_ral_paint` (material: `MAT-VOPSEA-RAL-CANT-{30,60,80,100}MM` keyed by `return_depth_mm` tier, labor: `RETURN_CANT_RAL_PAINT_LABOR`), following the `sablon_montaj_hartie`/`sablon_montaj_forex` pattern exactly.
2. Add a `pricing_rule_code`-keyed minimum-charge branch in `commercial_price_proposal_service.py` (same pattern as `ACM_BOXED_ASSEMBLY_M2_MIN`) enforcing the owner-documented 100 RON/RAL-color floor — **move the existing two `MIN_EUR` imports to top-of-file at the same time** (fixes the pre-existing inline-import debt noted in `01-commercial-law-matrix.md` §0 instead of copying it forward).
3. Gate `finisaje_colantare_vopsire` off for `face_finish_type=none` (stop charging 35 RON/m² for "no finish"); narrow its remaining scope to genuinely un-branched cases only (print/laminate face, until that gets its own rule).
4. Request explicit Owner confirmation before adding face-Oracal rows (the one open question flagged in the matrix §3) — do not silently treat "blocked" in `canonicalFinishEnumMap.ts` as inapplicable to this engine.
5. Leave Oracal color-tier, ACM mass color/mirror/other shell finishes untouched — these are `OWNER_COMMERCIAL_RULE_REQUIRED`, not implementable without new Owner input.

### G2 — ACM inclusion honesty (frontend)
1. Introduce one derived boolean (e.g. `isAcmPanelIncludedInOffer`) computed once, upstream of all 4 surfaces in §3, from the same source the CPP pricing engine already treats as authoritative (i.e., whichever payload field actually drives `always_include`/module activation for ACM lines today).
2. Make `intakeV4QuoteGeometry.ts:501`'s "standby" warning conditional on that same boolean instead of firing unconditionally for `support_panel`/`bond_panel` roles.
3. Make `IntakeV6ProductCompositionPanel.tsx`'s "Inclus în propunere"/"standby" chip read the same boolean.
4. Add an ACM line to `intakeV6ConfirmSummary.ts`'s view model and surface it in `IntakeV6ConfirmDashboard.tsx`'s `buildFinishSummaryLine()` (Step 3 recap) whenever the boolean is true.
5. Split the Step 1 composition card's single "Confirmă" into two explicit decision points (mandatory letters vs optional ACM) per A-F2 — smallest version is a second checkbox/button bound to the same boolean from step 1, not a new backend field.

### G3 — ACM standalone geometry validator (backend)
1. In `commercial_price_proposal_service.py`'s geometry-missing check (`_missing_critical_geometry`/`CRITICAL_GEOMETRY_KEYS`), branch by template: `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` should validate against ACM-shaped fields (`panel_width_mm`, `panel_height_mm`, `acm_thickness_mm`, `return_depth_mm`) instead of the letter-shaped `CRITICAL_GEOMETRY_KEYS` set (`letter_count`, `letter_face_area_m2`, etc.) currently hardcoded module-wide.
2. This unblocks live testing of ACM mass-color/mirror/shell-finish rules once G1-equivalent rows exist for them — but per the matrix, those rows still need Owner input first, so G3 alone only proves the *pipe* works (same role as the `sablon_montaj` positive control), not that ACM finish differentiation is priced.

### G4 — Finish contract vocabulary (backend schema + frontend token alignment)
1. Constrain `backend/schemas/intake_v4.py` `face_finish_type`/`return_finish_type`/`face_oracal_code` from bare `str | None` to a `Literal` covering the values actually reachable from the live UI combobox, OR — if a wider server-side vocabulary is intentional — add an explicit comment/test documenting that and why (per AGENT-B-F004's own recommended remediation).
2. Reconcile the short-token (`white`/`black`) vs suffixed-token (`white_aluminum`/`black_aluminum`) mismatch between the live UI emitter and `canonicalFinishEnumMap.ts`/schema defaults — add a normalization layer at the UI boundary rather than widening the schema to accept both silently.
3. Resolve the `mirror_silver` UI-reachability question (`OWNER_DECISION_REQUIRED` in the matrix) — either expose it as a selectable cant option or document it as intentionally deferred/vestigial.

### Cross-cutting recommendation: fail-closed `COMMERCIAL_RULE_MISSING` at selection granularity
`commercial_price_proposal_service.py:786-794` already raises `COMMERCIAL_RULE_MISSING` as a **critical blocker** (line 688, blocks `status="ready"`) — but only at the **module** level (`mod in CRITICAL_MODULE_CODES and mod not in covered_modules`). Recommend extending the same blocker code to fire when a specific **selection** inside an active module has no matching rule (e.g. `face_finish_type="print_laminate"` selected but no rule branches on it) — this closes AGENT-B-F001/F006/F007's whole class of "silently price the wrong thing" defects at the framework level, not just per-finding. This reuses an existing blocker code; it does not require inventing a new one.

---

## 10. Files expected to change (by group)

| Group | Backend | Frontend |
|---|---|---|
| G1 | `backend/data/commercial_rules_volumetric_v2.py`, `backend/services/commercial_price_proposal_service.py` | — |
| G2 | — (unless the "authoritative ACM inclusion" source turns out to live server-side in `product_definition_builder_service.py`/`ProductDefinitionPreview` — verify before starting) | `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.ts`, `frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx`, `frontend/src/lib/intakeV6/intakeV6ConfirmSummary.ts`, `frontend/src/components/workos/intake-v6/IntakeV6ConfirmDashboard.tsx` |
| G3 | `backend/services/commercial_price_proposal_service.py`, `backend/services/acm_quote_input_helpers.py` | — |
| G4 | `backend/schemas/intake_v4.py` | `frontend/src/features/product-system/canonicalFinishEnumMap.ts` (token alignment only, no new entries without Owner GO) |

No file above is in the AGENTS.md protected list (CostEngine/Status lifecycle/Snapshots/WorkIntake V1/QuoteWizard handoff/ProductSystem template registry).

---

## 11. Risks / rollback

- **Risk — G1 face-Oracal ambiguity:** if the Owner says the Product-System "blocked" tag *does* apply to the legacy CPP engine too, G1 must ship cant-only (Oracal wrap + RAL) and explicitly leave face-Oracal as `OWNER_COMMERCIAL_RULE_REQUIRED` rather than guessing. Mitigation: ask before writing the face rows; cant rows are unambiguous and can ship independently.
- **Risk — "Fără finisaj" gate change shifts existing totals** for any in-flight workspace that currently (incorrectly) gets charged 35 RON/m² for no finish. Mitigation: this is a correctness fix the audit already flagged as a defect; any workspace relying on the old (wrong) total was never commercially correct to begin with — no rollback path preserves incorrect pricing, but flag to Owner that historical draft totals will change on re-preview.
- **Risk — G2's "single boolean" refactor touches 4 files at once.** Mitigation: land the derived-boolean helper first (pure function, no behavior change), then switch each of the 4 consumers over one PR/commit at a time, verifying screenshots at each step per `ui-is-owner-reality` rule.
- **Risk — extending `COMMERCIAL_RULE_MISSING` to selection granularity could newly block workspaces that were previously silently mispriced.** This is the intended effect (fail-closed is safer than silent wrong pricing) but means some in-flight quotes will flip from `ready` to `blocked` on next preview. Mitigation: this must ship in the same PR as the G1 rule rows that resolve the now-visible gaps (RAL, Oracal cant), not before — otherwise it blocks cases G1 hasn't fixed yet.
- **Rollback:** every change in G1–G4 is additive (new rule rows, new gate conditions, new schema `Literal` constraints, new view-model field) or a narrowing of an already-flagged-wrong unconditional rule. Standard git revert of the specific commit is sufficient; no data migration, no snapshot rewrite, no irreversible state change identified.

---

## 12. Return to Lead

See `03-return-to-lead-summary.md` for the consolidated GO/NO-GO, exact ID lists, and Agent A/B/C file-ownership split for implementation.
