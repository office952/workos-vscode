# Decision log — Intake V6 Step2 layer UI + mounting + readiness UX

**Plan:** [plan.md](./plan.md)  
**Date:** 2026-07-16  
**Fixture workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Method:** PLAN MODE, docs-only amendment; read-only API/code inspection; no product-code changes.

---

## D1 — Shared LayerCardShell (Approach B)

**Decision:** Shared shell + letter/logo adapters; collapsed summary includes labeled Spate; no editable select when collapsed; expanded Fata→Cant→Spate.

**Rejected:** CSS-only patch; fully separate letter/logo card trees; schema-driven section engine for this GO.

**Why:** Root cause is structural (backing rendered outside expand gate), not CSS.

---

## D2 — Mounting installation_template sentinel

**Decision:** Persist `{ kind: "installation_template", template_code: null, configuration: {} }` for template-only / no ACM|bars. Readiness accepts only with template enabled + complete template fields. Bare null still `MOUNTING_SOLUTION_MISSING`.

**Rejected:** null-ok when checkbox on; reusing `backing_mode`; inventing common-panel field now.

**Why:** Distinguishes intentional template-only from unfinished decision; keeps PD free of metal/ACM child.

---

## D3 — Readiness banner in same Step2 phase

**Decision:** Compact count summary + expandable actionable details; map known runtime codes; forbid generic technical sentence when codes exist; severity split (blockers red / warnings amber).

**Rejected:** Deferring banner to a later UX-only ticket; deleting residual/missing-tariff protections without classification; greenwashing `contains_missing_prices`.

**Why:** Same operator boundary as cards/mounting; oversized generic panel blocks Confirm comprehension.

---

## D4 — Message classifications (fixture-grounded)

| Message | Classification | Disposition in Step2 |
|---------|----------------|----------------------|
| Residual vector | WARNING_ACTIONABLE (+ wording FALSE_POSITIVE risk) | Keep protection; improve copy/provenance; drive confirm finishes |
| Missing tariff (breakdown flag) | FALSE_POSITIVE candidate (no priced-row hits) | Detail UI + tests; no registry edits |
| Generic technical blockers | DUPLICATE / STALE wording over BLOCKING mounting | Map `MOUNTING_SOLUTION_MISSING`; drop generic when mapped |
| Mounting missing | BLOCKING_ACTIONABLE | U4 sentinel |
| pricing_adapter_not_ready | WARNING_ACTIONABLE (pricing phase) | Surface only |
| operator_confirmation_missing on Review | INFORMATIONAL | Confirm-step scoped |

---

## D5 — Logo template registry vs linked runtime

**Decision:** Treat `TPL-VOLUMETRIC-LOGO_v1` as **linked child code** under letters root for Step2 UI provenance. Do not require Product System catalog visibility for Step2 GO. Document DB availability absence separately; do not seed/reactivate logo in Step2 unless owner expands scope.

**Evidence:** Composition confirmed includes logo template; template-availability API returns **no LOGO rows** on fixture DB; material-breakdown still emits namespaced linked-logo lines.

---

## D6 — Pricing scope boundary

**Decision:** Step2 GO is configuration + readiness UX only. Next mandatory phase is **GRADI-CURAT PRICING TRUTH AUDIT** before ProductAggregate/commercial continuation and Quote/Order E2E.

**Rejected:** Fixing RON/EUR, VAT, CPP/EIC, or double-count quantities inside Step2.

---

## D7 — Recommended delivery order

1. Step2 UI + mounting + readiness UX  
2. GRADI-CURAT PRICING TRUTH AUDIT  
3. ProductAggregate / commercial continuation  
4. Quote / Order same-scenario E2E  

---

## Owner gates (resolved 2026-07-16)

### G1 — YES
Accept compact banner contract wording (RO count summary):
`N probleme blocheaza Confirmarea · M avertismente`.
Banner compact, expandable, action+target, disappears after resolve; do not mix warnings with blockers.

### G2 — YES
Accept residual copy shift toward “neconfirmat” when roles exist.
Perimeter protection retained; check not deleted.

### G3 — YES — DOCUMENT-ONLY
Accept logo catalog absence as out-of-scope for Step2.
No seed / auto-reactivate / template creation / Product System redesign.
`TPL-VOLUMETRIC-LOGO_v1` catalog follow-up after pricing/provenance audit.

### G4 — YES
GO to implement U1–U7 as one Step2 phase (no numerical pricing changes).
