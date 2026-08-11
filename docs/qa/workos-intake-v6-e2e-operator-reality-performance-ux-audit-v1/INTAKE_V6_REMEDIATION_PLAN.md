# INTAKE_V6_REMEDIATION_PLAN

Ordered slices. Prefer shared fixes. No implementation in this audit GO.

## Slice 0 — FIRST (P0) — Face finish token fidelity

**Root:** PRODUCT_TRUTH_TO_CPP_MAPPING  
**Touch:** `intake_v4_pricing_input_service` (+ CPP gate consumption of handoff raw/series if needed)  
**Behavior:** Operator `oracal_641/651/8500/none/print` must produce matching CPP face lines on dry-run  
**Risk:** Medium (adapter is shared) · **Schema:** 0 · **Pricing catalog:** 0 (use existing rules)  
**Tests:** dry-run/CPP matrix face series; Owner workspace repro without silent vinyl collapse  
**UI:** No required (may add honesty badge if incomplete)  
**Proof:** live dry-run contains `finisaje_oracal_641_material` when UI shows 641

## Slice 1 — P1 — Critical-path GET diet

**Root:** FRONTEND_ORCHESTRATION_OVERLOAD  
**Touch:** ReviewStep effects + `intakeV6ReviewRefetchDomains`  
**Behavior:** Finish change refreshes offer-critical GETs only; production/diagnostic lazy  
**Risk:** Low–Med · **UI:** No layout redesign required  
**Target:** official price refresh <1 s typical LAN  
**Proof:** network trace after face/cant change shows ≤4–5 GETs

## Slice 2 — P1 — Save/recalc feedback

**Root:** STATE_INVALIDATION + UX  
**Touch:** Review live rail  
**Behavior:** Explicit “salvat” / “recalculez Oferta…”; avoid blank without message  
**Risk:** Low

## Slice 3 — P1 — Back bevel / depth commercial honesty

**Root:** PRICING_RULE_NOT_CONSUMED  
**Touch:** CPP rules **or** UI honesty if Owner decides non-commercial  
**Owner decision required:** price bevel/depth vs label as production-only  
**Do not silent no-effect**

## Slice 4 — P2 — Vocabulary + diagnostic demotion

**Root:** UI_TECHNICAL_LEAKAGE  
**Touch:** face options, cant labels, offer vs cost chrome, technical accordion  
**Material vs finish separation**

## Slice 5 — P2 — Parallel read-model declutter

Lazy logical-list alternatives; ACM provisional clearly non-Ofertă; checklist sync with group confirm.

## Slice 6 — P3 — Dead code / unused derives

`activeTasks`, duplicate spine dry-run, etc.

---

## Minimal interactive chain (recommendation)

```text
UI → finish-setup save → priced-quote-dry-run (canonical money)
→ commercial_totals → live rail
```

Diagnostics / production / PD / spine: **lazy or Confirm-only**.  
Do **not** invent a new mega-endpoint until Slice 0–1 prove insufficient.

## Complexity estimates

| Slice | Complexity |
|-------|------------|
| 0 | M |
| 1 | M |
| 2 | S |
| 3 | M–L (Owner commercial decision) |
| 4 | S–M |
| 5 | M |
| 6 | S |
