# F7E Stage A — Return to Lead

Read-only research complete. No production code touched. Full detail in `00-exact-f7d-finding-register.md`, `01-commercial-law-matrix.md`, `02-architecture-proposal.md`.

## Exact P0/P1 IDs

```
P0 (4, exact — was reported as "4" by F7D Lead verdict, now reconciled with a full trail):
  AGENT-B-F001  — customer total insensitive to face/cant finish selection
  AGENT-B-F002  — EIC/CPP disconnect, margin exposure on >3x known cost spread
  F1/B-F005     — ACM inclusion status contradicted across 4-5 surfaces (merged dedup)
  A-F4          — Step 3 recap omits ACM panel already priced into the total

P1 (4, exact — F7D Lead verdict said "5 (approx.)"; corrected here to 4 because
    AGENT-B-F005 is folded into the P0 cluster above, not counted twice):
  A-F2            — single "Confirmă" bundles mandatory + optional ACM component
  A-F3            — raw internal ownership-doc copy rendered to operator
  AGENT-B-F003    — ACM standalone template blocked by letter-shaped geometry validator
  AGENT-B-F004    — finish-type schema fields are unconstrained free text
```

P2 = 7 (reference), P3 = 6 (reference, 2 of which are Agent B's own "confirmed correct" positive controls, not defects). Full row-by-row register with root-cause mapping in `00-exact-f7d-finding-register.md`.

## GO vs OWNER_RULE_REQUIRED by finish branch

| Branch | Verdict |
|---|---|
| Oracal cant wrap | **GO** — rates + ownership proven, matches existing `material_gate_path` pattern |
| Vopsit RAL (cant) | **GO** — rates, labor, and the 100 RON/color minimum are all owner-confirmed; minimum-charge mechanism already proven elsewhere |
| Stock cant colors | **GO (no-op)** — already correct by design, zero-delta confirmed, keep as regression fixture |
| Oracal face (641/651/8500) | **GO with one Owner confirmation first** — rates fully proven, but `canonicalFinishEnumMap.ts` tags face-Oracal `activationStatus="blocked"` pending a Product-System FACE workshop; ask whether that block reaches the separate legacy CPP engine before writing these rows |
| "Fără finisaj" being charged 35 RON/m² | **GO — this is a defect fix, not a rate question**; ungate it now regardless of the other branches' timing |
| Oracal color-tier (same series, different code) | **OWNER_COMMERCIAL_RULE_REQUIRED** — no policy exists either way; do not invent one |
| ACM mass color | **OWNER_COMMERCIAL_RULE_REQUIRED** — no canonical entry, no rate; also blocked live by AGENT-B-F003 |
| ACM mirror | **OWNER_COMMERCIAL_RULE_REQUIRED** — nothing exists (do not conflate with `mirror_silver`, a separate cant stock-color token) |
| Other ACM shell finishes (print/laminate, Oracal-wrapped shell) | **OWNER_COMMERCIAL_RULE_REQUIRED** — same as mass color |
| Print/laminate face (letters) | **OWNER_COMMERCIAL_RULE_REQUIRED** — material rate exists in registry but `canonicalFinishEnumMap.ts` author was not certain which registry keys are authoritative |

## Recommended file-ownership split for implementation (Agents A/B/C)

- **Agent A — Frontend ACM inclusion honesty (G2).** Files: `intakeV4QuoteGeometry.ts`, `IntakeV6ProductCompositionPanel.tsx`, `intakeV6ConfirmSummary.ts`, `IntakeV6ConfirmDashboard.tsx`. Closes F1/B-F005 (P0), A-F4 (P0), A-F2 (P1). Verify first whether the "authoritative ACM inclusion" boolean should be server-sourced from `ProductDefinitionPreview` before committing to a pure-frontend derivation.
- **Agent B — Backend commercial rule authoring (G1) + geometry validator (G3).** Files: `commercial_rules_volumetric_v2.py`, `commercial_price_proposal_service.py`, `acm_quote_input_helpers.py`. Closes AGENT-B-F001, F002, F006, F007 (via new gated rows + the "Fără finisaj" ungate + selection-granularity `COMMERCIAL_RULE_MISSING`), and AGENT-B-F003 (template-aware geometry validation). Owns the one Owner-confirmation checkpoint (face-Oracal) before proceeding past cant-only rows.
- **Agent C — Contract vocabulary + UX/copy hygiene (G4 + G5).** Files: `backend/schemas/intake_v4.py`, `canonicalFinishEnumMap.ts` (token alignment only), plus the P2/P3 UX-hygiene items (A-F3, A-F5, A-F6, A-F7, A-F9, A-F10, A-F11) which are independent of G1-G3 and can proceed in parallel without blocking the P0 gate.

This split keeps each agent inside one architectural layer (frontend-inclusion-state vs backend-pricing-rules vs contract-hygiene), matches the root-cause map in `00-exact-f7d-finding-register.md` §3, and lets G1/G2/G3 ship independently since none of their file sets overlap.

## GO/NO-GO for implementation

**GO for a scoped remediation build**, with three explicit conditions carried forward from this research:

1. Before Agent B writes face-Oracal commercial rules, get an explicit Owner answer to the one open question in `02-architecture-proposal.md` §9 (does the Product-System "FACE workshop blocked" tag apply to the legacy CPP engine too). Cant-Oracal and RAL rows have no such ambiguity and can start immediately.
2. Do not attempt ACM mass-color/mirror/other-shell-finish pricing in this build — those are `OWNER_COMMERCIAL_RULE_REQUIRED` with no existing rate to branch on; G3's geometry-validator fix only proves the pipe works, it does not price anything new.
3. Ship the selection-granularity `COMMERCIAL_RULE_MISSING` extension (§9 cross-cutting recommendation) **in the same PR as** the G1 rule rows that resolve the gaps it will newly surface, not before — otherwise it blocks workspaces G1 hasn't fixed yet.

No protected area (CostEngine, Status lifecycle, Snapshots, WorkIntake V1, QuoteWizard handoff, ProductSystem template registry) is touched by this scope. Standard commit-level revert is sufficient rollback for every proposed change — see `02-architecture-proposal.md` §11 for the full risk list.
