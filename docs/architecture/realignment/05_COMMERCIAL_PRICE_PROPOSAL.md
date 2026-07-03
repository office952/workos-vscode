# CommercialPriceProposal — Client Commercial Price Model

**Version:** 1.0.0  
**Status:** Target architecture (documentation only) — **MISSING runtime today**  
**Step:** 7G (read-only preview — NEEDS OWNER GO)

---

## 1. Rolul sistemului

CommercialPriceProposal este modelul țintă pentru **prețul propus către client** — bazat pe produs/soluție, reguli comerciale și geometrie — **nu** pe minute × tarif oră.

**Regulă centrală:** CommercialPriceProposal **NU este** `minute × rate`. P-Media nu ofertează „100 ore × tarif”.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Preț propus client** | commercial_subtotal, commercial_total, currency |
| **Linii comerciale** | commercial_lines[] per zonă/modul |
| **Reguli comerciale** | Formule mp/ml/buc/literă/set/minim |
| **Formule comerciale** | rule_id, basis, unit_price, min_job |
| **Complexitate** | Coeficienți, urgență |
| **Valoare comercială** | Policy owner |
| **Marjă țintă** | Applied to **commercial base** — not necessarily cost-plus |
| **Variante ofertă** | Opțiuni A/B dacă policy |
| **Provenance** | rule_provenance[] — ce regulă a generat linia |
| **Warnings** | Marjă mică vs EstimatedInternalCost — **non-blocking by default** |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Minute reale / ore estimate ca basis primar |
| `rate_per_hour` ca formulă client |
| Task sessions |
| Cost real post-job |
| ExecutionActuals |
| ProfitabilityAnalysis final |
| Modificare retroactivă post-accept |
| `total_internal_cost × margin` ca singură formulă universală |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Intake V6 | Geometrie, finish groups, LED, mounting |
| ProductDefinition | Module active |
| ProductAggregate | Structure keys, zones |
| Commercial Price Rules Registry | mp/ml/buc/set/minim rules (Step 7I) |
| Owner policy | Urgency, complexity, minimum job |

**NU citește ca basis primar:** workcenter_rates.rate_per_hour, estimated_minutes.

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| CommercialPriceProposal JSON | Quote snapshot (Step 8) |
| Preview UI (7G) | Operator review — read-only |
| Margin preview warnings | Compared to EstimatedInternalCost |
| Client-facing PDF/email (future) | From snapshot only |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Preț comercial ofertat | **TARGET source of truth** at quote snapshot |
| Today wrongly aliased | `QuotePrice.final` from cost_plus via `/price` |
| Intake live offer | **NOT** — preview only |
| Cost Engine total | **NOT** |

---

## 7. Conexiuni cu celelalte sisteme

```
Intake V6 + ProductAggregate
    ↓
CommercialPriceProposal (THIS) ← Commercial Price Rules Registry
    ↓
Quote Snapshot.commercial_price (Step 8)
    ↓
Order (frozen commercial promise)
    ↓
ProfitabilityAnalysis compares quoted commercial vs actual economics
```

| Sistem | Relație |
|--------|---------|
| EstimatedInternalCost | Side-by-side — poate genera warning marjă |
| Cost Engine | **NU** generează CommercialPriceProposal |
| QuoteOrchestrator._apply_commercial | **FROZEN** — cost-plus deviated |
| ExecutionActuals | **NU** modifică proposal acceptat |

---

## 8. Reguli owner obligatorii — volumetric letters

| Zonă | Regulă comercială |
|------|-------------------|
| CNC față/spate | lei/ml — material, grosime, sanfren |
| Modelare cant aluminiu | lei/ml |
| Vopsire/finisaj | lei/m² sau minim lucrare |
| LED | lei/modul, lei/set sau mp luminat |
| Asamblare | lei/literă, lei/set sau pachet |
| Șablon montaj | lei/m² sau fix |
| Ambalare | fix / minim |
| Montaj șantier | fix / per locație / complexitate — **nu** automat oră |

**Debitare spate:** ml vs m² — **NEEDS_OWNER_DECISION** (UNKNOWN final basis).

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Model missing | No runtime CommercialPriceProposal | `NEEDS_OWNER_DECISION` |
| QuoteOrchestrator cost-plus | final = f(total_cost, margin) | `HIGH_RISK_WRONG_DIRECTION` |
| Intake live calc | Client-side buckets + markup | `MISLEADING_UI` |
| /price single number | No commercial line provenance | `FROZEN_UNTIL_REALIGNED` |
| WC rate blocks offer | Conflated with commercial | `HIGH_RISK_WRONG_DIRECTION` |

---

## 10. Target state (Step 7G)

| Aspect | Țintă |
|--------|-------|
| Schema + preview API | Read-only, no DB quote write |
| commercial_lines[] | Per zone with rule_provenance |
| Blockers | Geometry missing, commercial rule missing — **NOT** rate_per_hour |
| UI label | „Propunere comercială” — distinct from internal estimate |
| Hardcoded rules OK | Initial pilot volumetric — registry later (7I) |

**Endpoint/model țintă (conceptual):**

```
POST /api/v1/commercial-price-proposal/preview  (dry_run, no persist)
Response: {
  commercial_lines[], commercial_subtotal, commercial_total,
  currency, rule_provenance[], warnings[], blockers[]
}
```

---

## 11. Forbidden behavior

| Interzis |
|----------|
| minute × rate_per_hour as primary line |
| Derive commercial solely from Cost Engine total |
| Persist as official quote without Step 8 snapshot |
| Block offer on missing WC hourly rate |
| Retroactive change from ExecutionActuals |
| Implement 7G runtime without owner GO |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Volumetric lines | All active zones have commercial rule or explicit blocker |
| Provenance | Each line traceable to rule_id |
| Separation | commercial_total ≠ estimated_internal_cost path |
| No hourly lines | Audit grep clean on commercial output |
| Preview labeled | UI not misleading (Step 11) |
