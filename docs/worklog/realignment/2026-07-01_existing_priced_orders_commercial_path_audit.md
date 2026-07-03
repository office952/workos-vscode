# Existing Priced Orders Commercial Path Audit

Date: 2026-07-01  
Scope: trace all three non-zero orders visible in the Oferte/Orders UI; classify their commercial path; identify what can and cannot be ported to V6.

---

## 1. Orders Traced

| Order code | Visible total | DB id | Status | quote_id | quote_snapshot_v2_id |
|---|---|---|---|---|---|
| ORD-IV6-V2-1782815703-1 | 12.50 RON | 88002 | locked | 1 | 3 |
| ORD-QA-V2-READINESS-88001 | 1,500.00 RON | 88001 | locked | 88001 | 1 |
| O-E2E-SPRINT33 | 1,398.25 RON | 1 | locked | — | — |

Note: the first order was displayed in the UI as `ORD-TV6-...` (UI rendering artefact); the real DB code is `ORD-IV6-V2-1782815703-1`.

---

## 2. DB Source of Visible Totals

### ORD-IV6-V2-1782815703-1 (12.50 RON)

- `orders.total_amount = 12.5`
- `orders.snapshot_v2_json.accepted_commercial_total = 12.5`
- `orders.snapshot_v2_json.commercial_price_proposal_snapshot.subtotal_commercial = 12.5`
- `orders.snapshot_v2_json.commercial_price_proposal_snapshot.status = "blocked"`
- All cpp line subtotals in the snapshot are `null`
- The linked quote (id=1) has `grand_total=0.0`
- No quotes in the DB have a positive `grand_total`

The 12.5 RON = the letter perimeter of workspace `96009ff3-a20b-40d7-a8c7-540e48058526` (12.5 ml). The old code (Sprint 8) may have used `documented_unit_price=1.0` RON/ml as a placeholder, producing `12.5 ml × 1.0 = 12.5 RON`. That placeholder was later removed from the commercial rules, but the stored snapshot retains the value. The commercial proposal status at the time was `"blocked"` — it was never a valid ready price.

### ORD-QA-V2-READINESS-88001 (1,500.00 RON)

- `orders.total_amount = 1500.0`
- `orders.snapshot_v2_json.accepted_commercial_total = 1500.0`
- `orders.snapshot_v2_json.commercial_price_proposal_snapshot.status = "ready"`, `subtotal_commercial = 1500.0`
- `orders.snapshot_v2_json.commercial_price_proposal_snapshot.commercial_price_lines = []` (EMPTY — no line items)
- `orders.snapshot_v2_json.content_hash = "abc123def456abc123def456abc123de"` (not a real SHA256)
- `orders.snapshot_v2_json.provenance = []`, `input_summary = {}`
- `quote_snapshots_v2.id=1`: `status=frozen`, `snapshot_json=null`, `workspace_id=null`
- Quote 88001 exists but `grand_total=0`

The 1,500.00 RON was written directly into the seeded fixture with `cpp.status=ready` and a fake subtotal, no real commercial line items.

### O-E2E-SPRINT33 (1,398.25 RON)

- `orders.total_amount = 1398.25`
- `orders.notes = "Seeded by scripts/seed_canonical_order_for_e2e.py (Sprint #33). Canonical snapshot for execution plan 201 smoke. Do not mutate."`
- `orders.quote_id = null` (no linked quote)
- `orders.snapshot_line_items.product_definition.product_type = "Totem"` (not volumetric letters)
- `orders.snapshot_line_items.final_price = {net: 1175.0, gross: 1398.25}`
- No real commercial rules for volumetric letters

---

## 3. Linked Quotes and Snapshots

| Order | Linked quote grand_total | Snapshot status | Snapshot commercial path |
|---|---|---|---|
| ORD-IV6 | 0.0 (quote id=1) | quote_snapshots_v2 frozen | cpp.status=blocked, lines=null subtotals |
| ORD-QA | 0.0 (quote id=88001) | quote_snapshots_v2 frozen (null json) | cpp faked with status=ready, no real lines |
| E2E-SPRINT33 | — (no quote) | — | Seeded final_price object, Totem product |

**Finding**: No quote in the database has a positive `grand_total`. All visible order totals come from `orders.total_amount` which was written directly (via seed script, fixture, or old E2E path). No real pricing engine path ever populated `quotes.grand_total` successfully.

---

## 4. Working Commercial Path Classification

| Order | Classification | Evidence |
|---|---|---|
| ORD-IV6-V2-1782815703-1 | **E: DATA_FIXTURE_ONLY_NO_REAL_RULES_FOUND** | 12.5 = perimeter in ml, cpp was blocked, placeholder unit_price removed, quote.grand_total = 0 |
| ORD-QA-V2-READINESS-88001 | **E: DATA_FIXTURE_ONLY_NO_REAL_RULES_FOUND** | content_hash "abc123", empty cpp lines, 1500 RON with no calculation |
| O-E2E-SPRINT33 | **E: DATA_FIXTURE_ONLY_NO_REAL_RULES_FOUND** | explicitly seeded, different product (Totem), no linked quote |

All three are fixtures. **None demonstrate a real working commercial pricing path for volumetric letters.**

---

## 5. Extracted Line Items and Rules

### ORD-IV6 commercial_price_proposal_snapshot lines (from blocked old snapshot)

| Code | Basis | Quantity | Unit | unit_price | Subtotal | Module |
|---|---|---|---|---|---|---|
| debitare_fata | ml | 12.5 | ml | null | null | debitare_fata |
| modelare_cant_aluminiu | ml | 12.5 | ml | null | null | modelare_cant |
| debitare_spate | unknown | 1.2 | m² | null | null | debitare_spate |
| sistem_led_module | piece | 24 | buc | null | null | sistem_led |

All unit prices are null. All subtotals are null. The `subtotal_commercial = 12.5` in the snapshot predates the current code — it likely came from a placeholder `documented_unit_price=1.0` RON/ml that was later removed.

### ORD-QA commercial_price_proposal_snapshot lines

No lines. `commercial_price_lines = []`. The `subtotal_commercial = 1500.0` is a seeded value.

### O-E2E-SPRINT33 snapshot_line_items

Not volumetric letters. Uses `product_type=Totem`, ACP materials, CNC cut and assembly operations, dimensions-based pricing unrelated to volumetric letter commercial rules.

---

## 6. Intake 2 / V2 Path Findings

The V2/V4 draft quote path (`build_v4_quote_draft_payload`) explicitly produces **zero placeholders**:

```python
line_items = [
    {
        "productCode": ...,
        "description": ...,
        "quantity": qty,
        "unit_price": 0,  # explicitly zero
        "total": 0,        # explicitly zero
    }
]
```

And the resulting quote columns are all zero:

```python
"subtotal": 0.0,
"total_before_vat": 0.0,
"vat": 0.0,
"grand_total": 0.0,
```

The V4 draft quote was designed as an **internal review placeholder**, not a priced offer. This is why the V6 zero-quote fast guard was implemented — to block this legacy path from being treated as commercial truth.

The V4/V2 path cannot be ported to V6. It deliberately produces zero. The V6 backend priced dry-run/write path was built precisely to replace this zero placeholder with real commercial totals.

---

## 7. Sprint33 Findings

- Product: Totem (different product type)
- Pricing: hardcoded `{net: 1175.0, gross: 1398.25}` in `snapshot_line_items.final_price`
- Source: `scripts/seed_canonical_order_for_e2e.py` — a smoke test seed script for execution plan testing
- Commercial basis: not applicable (Totem, ACP, different operations)
- Verdict: **Not reusable for V6 volumetric letters. Different product, seeded total, no pricing engine.**

---

## 8. Comparison to V6 Blockers

### Current V6 commercial rules `documented_unit_price` status

| Rule code | Module | Basis | documented_unit_price | Blocker? |
|---|---|---|---|---|
| debitare_fata | debitare_fata | ml | **None** | No — but null price → null subtotal |
| modelare_cant_aluminiu | modelare_cant | ml | **None** | No — but null price → null subtotal |
| debitare_spate | debitare_spate | **unknown** | None | YES — `COMMERCIAL_BASIS_UNKNOWN` + `DEBITARE_SPATE_BASIS_ML_VS_M2` |
| sistem_led_module | sistem_led | piece | **None** | No — but null price → null subtotal |
| sursa_led | sistem_led | piece | **None** | No — but null price → null subtotal |
| finisaje_colantare_vopsire | finisaje | m2 | **None** | No — but null price → null subtotal |
| sablon_montaj_hartie | finisaje | m2 | **5.0 EUR/m²** | Only documented price in the system |
| sablon_montaj_forex | finisaje | m2 | **None** | YES — `SABLON_FOREX_COMMERCIAL_PRICE` (workspace has forex sablon active) |
| ambalare | finisaje | fixed | None | YES — `AMBALARE_COMMERCIAL_RULE` (optional) |
| montaj | finisaje | fixed | None | YES — `MONTAJ_COMMERCIAL_RULE` (optional) |

### V6 blocker comparison

| Blocker | Module | Priced order proves this? | Evidence | Owner decision needed? | Recommended fix |
|---|---|---|---|---|---|
| COMMERCIAL_BASIS_UNKNOWN | debitare_spate | No | ORD-IV6 snapshot also blocked with unknown basis | YES — ml or m²? | Owner decides: debitare_spate basis |
| DEBITARE_SPATE_BASIS_ML_VS_M2 | debitare_spate | No | All orders have null subtotals for this line | YES | Owner decides: ml (perimeter) or m² (area) for back CNC |
| SABLON_FOREX_COMMERCIAL_PRICE | finisaje | No | Not referenced in any order | YES — price for Forex sablon? | Owner decides: is Forex sablon separate commercial line? If yes, what price/m²? |
| AMBALARE_COMMERCIAL_RULE | finisaje | No | No packaging line in any order | YES — include in price or separate? | Owner decides: included or separate line at what price |
| MONTAJ_COMMERCIAL_RULE | finisaje | No | Not referenced in any priced order | YES | Owner decides: out of scope, external service, or fixed line? |

**Critical additional finding**: Even resolving all four structural blockers would not produce a non-zero total, because `documented_unit_price=None` for all critical lines except sablon_hartie. The `subtotal_commercial` would still be `None` (no line can compute a subtotal without a unit price). This means:

To make the V6 dry-run READY and non-zero, the owner must also provide:
- RON/ml price for `debitare_fata`
- RON/ml price for `modelare_cant_aluminiu`
- RON/ml or RON/m² price for `debitare_spate` (after deciding basis)
- RON/buc price for `sistem_led_module`
- RON/buc price for `sursa_led`
- RON/m² price for `finisaje_colantare_vopsire`

---

## 9. What Can Be Reused in V6

- **Commercial rule structure**: correct (ml for perimeter cuts, m² for area, piece for LED, fixed for optional services). Reuse.
- **Commercial rule basis names**: `ml`, `m2`, `piece`, `fixed`, `m2`. These match the commercial policy. Reuse.
- **sablon_hartie price (5 EUR/m²)**: owner-documented. This is the only real commercial unit price in the system. Reuse.
- **Optional criticality for ambalare and montaj**: correct. These should not block the dry-run from returning ready when the only issues are non-critical optional decisions. Reuse.

---

## 10. What Must NOT Be Reused

- The 12.5 RON from ORD-IV6. Not a real price, equals the letter perimeter, was from a blocked commercial proposal.
- The 1,500 RON from ORD-QA. Not a real price, was seeded directly with no line items.
- The V4 draft quote zero placeholder path. Deliberately produces zero; forbidden for V6 commercial truth.
- The Totem/ACP pricing model from E2E-SPRINT33. Different product type; operations, materials, and formulas do not apply to volumetric letters.
- Any commercial total computed from minutes × rate per hour. Forbidden by commercial contract.

---

## 11. Final Recommendation

**B. OWNER_DECISIONS_REQUIRED_BEFORE_PRICING**

The audit proves:
1. No real commercial pricing engine has ever produced a meaningful, valid, non-zero total for V6 volumetric letters in this app.
2. All visible non-zero order totals are seeded fixtures or artifacts.
3. The commercial rule structure is correct, but all critical `documented_unit_price` values are `None`.
4. Even resolving the four structural blockers (debitare_spate, sablon_forex, ambalare, montaj) would not produce a non-zero total without owner-approved unit prices.
5. The only documented commercial price in the system is sablon_hartie at 5 EUR/m².

Owner must provide before the next V6 pricing implementation slice:

**Required owner decisions:**

1. `debitare_spate` commercial basis: ml (perimeter) or m² (area)?
2. `debitare_fata` unit price: RON/ml
3. `modelare_cant_aluminiu` unit price: RON/ml
4. `debitare_spate` unit price: RON/ml or RON/m² (after deciding basis)
5. `sistem_led_module` unit price: RON/buc
6. `sursa_led` unit price: RON/buc
7. `finisaje_colantare_vopsire` unit price: RON/m²
8. `sablon_montaj_forex`: separate commercial line (with what price/m²)? or internal-only?
9. `ambalare`: included in product price? or separate set/lucrare at what price?
10. `montaj`: out of scope (not included)? or external service at what price?

---

## 12. Next Safe Implementation Slice

Once the owner provides decisions for items 1–10 above, the next safe implementation slice is:

1. Update `backend/data/commercial_rules_volumetric_v2.py` with owner-approved basis and unit prices.
2. Re-run the real V6 dry-run for workspace `c8dda47f-e2a7-4fea-800c-2dc01b2be5a3`.
3. If the dry-run returns `V6_PRICED_DRY_RUN_READY` with positive non-zero totals, execute the guarded V6 priced write for quote #6.
4. If write succeeds, create Quote Snapshot V2.
5. Reload Oferte — the visible `grand_total` should then be non-zero.

Do not implement any of the above steps until owner decisions are confirmed in writing.

---

## 13. What Did Not Change

- No code was changed in this audit.
- No DB rows were modified.
- No quotes or orders were created, updated, or deleted.
- No snapshots were created.
- No commercial rules were patched.
- No frontend was changed.

---

## 14. Forbidden Confirmation

- No rollback to V2: confirmed
- No V6 dependency on V2/V4: confirmed
- No copied totals: confirmed
- No fake totals: confirmed
- No hardcoded gradi-curat price: confirmed
- No frontend preview copied: confirmed
- No order created: confirmed
- No ProductAggregate: confirmed
- No Task Graph: confirmed
- No ExecutionPlan: confirmed
- No Employee Mobile: confirmed
