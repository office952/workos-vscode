# Agent B — E2E Terminology Mismatches (F7D)

## 1. Live UI combobox values vs. backend/canonical intake tokens (cant/return finish)

| Live UI label (Romanian) | Live UI `<option value>` (observed in DOM, workspace 5a5ce742) | Backend schema default / canonical token (`schemas/intake_v4.py`, `canonicalFinishEnumMap.ts`) | Mismatch |
|---|---|---|---|
| Alb | `white` | `white_aluminum` | UI emits short form; schema default and canonical `intakeTokens` list use the `_aluminum` suffix. No mapping/normalization layer observed between them. |
| Negru | `black` | `black_aluminum` | Same pattern |
| Auriu | `gold` | `gold_aluminum` | Same pattern |
| Argintiu | `silver` | canonical list has `mirror_silver`, not `silver` | `silver` (stock aluminum, silver-colored) and `mirror_silver` (a distinct finish type, presumably reflective/mirror) appear to be **conflated or diverged** — the live UI's "Argintiu" (Silver) uses bare `silver`, while the canonical map's stock-color family lists `mirror_silver` as a separate token. Not clear if these are the same finish under two names or genuinely different finishes; not resolved in this audit — `OWNER_DECISION_REQUIRED`. |
| Vopsit RAL | `ral_paint` | `ral_paint` | Match |
| Oracal 651 | `oracal_wrapped` | `oracal_wrapped` (canonical) / `oracal_651` also appears as a synonym in `intakeTokens: ["oracal_wrapped", "oracal_651", "vinyl"]` | Match, but three synonymous tokens coexist for the same concept in the canonical map — a normalization/consolidation gap, not itself a pricing bug. |
| (not offered in live combobox) | — | `mirror_silver`, `standard_aluminum` | Backend/canonical vocabulary is **wider** than what the live UI exposes — these tokens are schema-legal (unconstrained `str`) and accepted by the API without error, but an operator can never actually select them through the current UI. |

## 2. Contract looseness — no enum/Literal validation on finish type fields

`backend/schemas/intake_v4.py`:

```
102: face_oracal_code: str | None = None
103: face_oracal_name: str | None = None
104: return_finish_type: str | None = "white_aluminum"
105: return_oracal_code: str | None = None
```

`return_finish_type` and `face_finish_type` are plain `str | None`, not `Literal[...]` or an `Enum`. Verified directly: submitting `return_finish_type: "mirror_silver"` (a value not present in the live UI's combobox at all) via the CPP preview endpoint returns `status: "ready"` with **no validation warning of any kind** — the backend silently accepts any string. This is a contract-hygiene gap: the "vocabulary" that actually reaches pricing logic is effectively unbounded, which makes it structurally easy for typos, deprecated tokens, or new UI values to silently produce the same (flat, zero-delta) commercial outcome without ever surfacing as an error.

## 3. "Ofertă client" (customer offer) vs. "Estimări pe produs" (per-product estimates) — two numbers, two meanings, easy to confuse

The operator-facing UI shows **two different figures** in the same sidebar region:

1. **`Ofertă client`** (top card) — sourced from `CommercialPriceProposalService.commercial_total`. This is the number that persists through Step 3 "Confirmare finală" and is what "Creaza oferta pretuita" (create priced offer) would use. **This is the number that does not change with finish selection** (the core P0).
2. **`Estimări pe produs` → "Litere" / "Panou Alucobond"** (lower card, per-component EUR figures) — explicitly labeled `"Nu înlocuiește deciziile de produs. Oferta client rămâne în rezumatul de mai sus."` ("Does not replace product decisions. The client offer remains in the summary above.") — this figure **did** move (+10.92 EUR) when the finish module first activated (none → Oracal 8500), which could easily be mistaken by an operator (or a less careful auditor) as proof that finish-sensitive pricing works, when it is actually a module-activation-gate effect, and the number that matters commercially (`Ofertă client`) never moved.

Recommend the terminology/UI review flag this dual-number presentation as a source of operator confusion, independent of the underlying pricing-rule defect.

## 4. "Confirmed" / "Unconfirmed" terminology vs. actual system behavior

Warning text: `"Unconfirmed finish groups may require owner review before numeric pricing."` implies a gating relationship between `confirmed: false` and whether "numeric pricing" happens. In practice, `confirmed: true`, `confirmed: false`, an empty `letter_group_finishes: []`, and an entirely absent `letter_group_finishes: None` all produce the **same** `status: "ready"` and the **same** numeric `commercial_total`. The word "unconfirmed" in the warning does not correspond to any different runtime behavior today.

## 5. "Product System" canonical finish map vs. live Intake V6 / CPP

`canonicalFinishEnumMap.ts` and its owner-decision doc use the term **"FINISH"** to mean a specific *component-ownership* concept in a not-yet-built "Product System" architecture (mutually exclusive from "RETURN-CANT" and "FACE" components). This is a different sense of "finish" than the live Intake V6 `finish_setup` payload / `finisaje` module, which is already runtime and already prices real quotes. Both use the word "finish"/"finisaj" but refer to architecturally distinct systems at different maturity stages — worth clarifying in any cross-team documentation to avoid conflating "the owner already decided this" (true, for the future Product System's component ownership) with "the live pricing engine already implements this" (false, for the live CPP audited here).

## 6. DEV_BRIDGE naming convention

Constants like `DEV_BRIDGE_FINISH_RON_M2`, `DEV_BRIDGE_SABLON_FOREX_RON_M2` in `commercial_rules_volumetric_v2.py` are internal code-only labels never surfaced to the operator UI. The UI shows a clean "Ofertă client" total with no visual indicator that any given line is an "interim/dev-bridge" placeholder rate versus an owner-finalized Pricing Registry rate. An operator creating a real offer today has no way to know from the UI which lines are provisional.
