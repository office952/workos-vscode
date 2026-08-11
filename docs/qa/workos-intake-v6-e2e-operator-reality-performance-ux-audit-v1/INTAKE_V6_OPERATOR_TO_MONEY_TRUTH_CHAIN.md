# INTAKE_V6_OPERATOR_TO_MONEY_TRUTH_CHAIN

HEAD: `303add0f` · Workspace probe: `IV6-362B31FC` (`03a1da1e-…`) · READ-ONLY

## Canonical chain

```text
operator UI
→ React draft (form / letterGroups)
→ PUT /finish-setup
→ payload_json.finish_setup
→ Product Truth (confirm/pin; freeze gate)
→ pricing-input-preview → quote_input
→ CPP (commercial_rules_volumetric_v2 / CommercialPriceProposalService)
→ priced-quote-dry-run → commercial_totals
→ live Ofertă rail / Confirm
→ priced write / freeze
```

## Stage ownership

| Stage | Owns | Must not own | Failure mode (observed) |
|-------|------|--------------|-------------------------|
| UI selection | Labels, tokens | Rates | Material conflated into finish label |
| React draft | Dirty local state | Persistence authority | Dominant flatten hides mixed layers |
| finish-setup PUT | Persist + normalize | Money | Autosave debounce delays truth |
| Product Truth | Confirmed bags / freeze | Live OFAT money | Checklist vs group.confirmed drift |
| quote_input adapter | Flatten for CPP | EUR catalog | **Token collapse: oracal_641 → vinyl / oracal_651** |
| CPP | Line money | UI labels | Gates miss collapsed tokens → missing lines |
| dry-run | Official totals | FE arithmetic | Fan-out lag; empty flash on invalidate |
| Live rail | Display official | Invent rates | “Tarife lipsă” while gross shown |
| Confirm | Gate + Ofertă | Second money authority | Final offer visible while handoff blocked |

## Critical runtime finding (Owner workspace)

| Layer | Face Oracal 641 |
|-------|-----------------|
| UI | Shows `Oracal 641 · 019 Signal yellow` |
| payload.finish_setup | `face_finish_type=oracal_641` |
| quote_input | `face_finish_type=vinyl`; handoff `face_finish_type=oracal_651`, raw=`oracal_641` |
| CPP dry-run lines | **No** `finisaje_oracal_641_material` / aplicare |
| Cant Oracal | Lines **present** (`finisaje_cant_oracal_*`) |
| Gross | 657.54 EUR (READY) without face vinyl money |

**Conclusion:** face commercial path is broken by adapter token drift; cant wrap/RAL can price when tokens survive; back bevel has no CPP gate (NO_EFFECT intentional under current catalog).

## Face / Cant / Back summary

| Domain | Should money move? | Observed |
|--------|-------------------|----------|
| Face none / 641 / 651 / 8500 / print | YES (CPP rules exist) | Adapter collapse → live may show **NO face line** despite UI |
| Cant stock colors | NO surcharge (catalog) | ZERO_DELTA intentional |
| Cant Oracal / RAL | YES | Works when `return_finish_type` preserved |
| Back Forex ± șanfren | Owner expects YES (CNC MB has bevel) | CPP `debitare_spate` ignores bevel → **NO_EFFECT** |
