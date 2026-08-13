# STEP2_COMPUTATION_DUPLICATION_GRAPH

```text
Step2 refresh (after discrete save)
│
├─ material-breakdown endpoint
│  └─ MB computation ........................ REQUIRED (sibling authority)
│
├─ pricing-input-preview endpoint
│  └─ pricing input ......................... REQUIRED (preview)
│
├─ priced-quote-dry-run endpoint
│  └─ pricing input → CPP → commercial_totals REQUIRED (official Ofertă)
│
├─ quote-handoff-preview endpoint
│  └─ handoff projection .................... REQUIRED (handoff)
│
├─ ai-informational-assist-candidate ........ DISPLAY_ONLY / non-critical
├─ product-system-binding ................... DISPLAY_ONLY / binding chrome
│
└─ logical-list-read-model endpoint
   ├─ MB computation ........................ DUPLICATE (same helper as sibling MB)
   ├─ priced dry-run ........................ DUPLICATE (full Option B dry-run again)
   │  └─ pricing input → CPP ................ DUPLICATE vs sibling PQ
   └─ logical projection .................... REQUIRED (VL row assembly)
```

| Computation | Mark |
|---|---|
| Sibling MB | REQUIRED |
| Sibling PQ / CPP | REQUIRED |
| LL nested MB | DUPLICATE |
| LL nested dry-run / CPP | DUPLICATE |
| LL VL projection from MB | REQUIRED |
| LL ACM/conn rows from dry-run commercial lines | DISPLAY_ONLY (composition detail; not Ofertă authority) |
| Offer lifecycle CURRENT | Depends on PQ only — CAN_DEFER LL |
