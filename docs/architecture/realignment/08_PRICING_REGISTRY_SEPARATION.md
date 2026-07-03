# Pricing Registry — Conceptual Separation

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**UI (read context):** `frontend/src/pages/Pricing.tsx`  
**Step:** 7I — NEEDS OWNER GO

---

## 1. Rolul sistemului

Pricing Registry administrează **reguli și prețuri de referință** — separat pe tip: materiale, reguli comerciale, reguli cost intern, capacity checks, analytics — **nu** un hub unic care amestecă totul într-o ofertă.

---

## 2. Ce detine

| Zonă țintă | Conținut |
|------------|----------|
| **Material Prices** | inventory_materials.unit_cost — achiziție |
| **Commercial Price Rules** | mp/ml/buc/literă/set/minim/complexitate/urgentă |
| **Internal Cost Rules** | Op rates non-hourly: ml/mp/buc/fix |
| **Capacity Check Rules** | Estimated effort thresholds — warnings |
| **Internal effort rates** | Optional — **not client commercial hourly** |
| **Markup policies** | Target: commercial policy — **not universal cost-plus** |
| **Analytics entries** | Post-job benchmarks — read-only |
| **Classifications** | Tag per entry (see §6) |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Tomberon materiale nefolosite fără clasificare |
| Preț pe oră client |
| Sursă universală pentru toate prețurile |
| Loc unde se amestecă material + WC + markup + quote fără separare |
| CommercialPriceProposal instance (runtime per job) |
| Quote snapshot |
| ExecutionActuals |
| Product structure truth |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Owner / admin | Rate entries, rule definitions |
| Inventory imports | Material costs |
| Architecture docs | Owner costing audit baselines |
| Template material maps | Which materials used per template (doc 13) |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Material unit_cost lookups | Cost Engine / EstimatedInternalCost |
| Commercial rule definitions | CommercialPriceProposal engine (7G) |
| Internal op rate lookups | Cost Engine (7H) |
| WC rates (reclassified) | Capacity + internal effort — **not client tariff label** |
| Registry metadata | Admin UI, audit |

---

## 6. Source of truth — clasificări

| Class | Meaning | Example |
|-------|---------|---------|
| `material_price` | Acquisition unit cost | MAT-VOPSEA-RAL unit_cost |
| `commercial_price_rule` | Client offer formula | CNC lei/ml by material |
| `internal_cost_rule` | Pre-production estimate | Forming lei/ml internal |
| `capacity_check_rule` | Non-blocking time threshold | Assembly hours warning |
| `analytics_only` | Post-job reference | Historical ml/min |
| `legacy/dead` | Unused or misleading | Orphan WC rate |

**workcenter_rates today:**

| Field | Today label | Target label |
|-------|-------------|--------------|
| rate_per_hour | „Source of truth” (misleading) | Internal effort / capacity — **not client hourly** |
| rate_per_linear_meter | Partial use | Primary internal + commercial basis where owner defines |

---

## 7. Conexiuni cu celelalte sisteme

```
Pricing Registry (separated tabs)
    ├→ Inventory (material_price) ──→ EstimatedInternalCost
    ├→ Commercial Price Rules ──→ CommercialPriceProposal
    ├→ Internal Cost Rules ──→ Cost Engine
    └→ Capacity Rules ──→ warnings (non-blocking commercial)

Quote Snapshot reads frozen copies at offer time — NOT live registry retroactive change
```

| Sistem | Relație |
|--------|---------|
| Cost Engine | Reads internal rules — not writes commercial |
| QuoteOrchestrator | Today reads mixed — **split** |
| ProductSystem | References material codes — not prices |
| ProfitabilityAnalysis | May suggest registry updates **future** |

---

## 8. Reguli owner obligatorii

1. Registry edits for „readiness” without commercial rule design — **FROZEN**.
2. No RAL/Oracal color registry → automatic CE rates (AGENTS.md).
3. TVA separate from stored rates (owner costing audit).
4. EUR base for volumetric owner ops — conversion notes documented, not live FX.
5. Each template: know used / optional / legacy / unused materials.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| Unified Pricing UI | Materials + WC + markup one page | `HIGH_RISK_WRONG_DIRECTION` |
| WC rate_per_hour as quote blocker | Missing rate → NOT_READY | `HIGH_RISK_WRONG_DIRECTION` |
| workcenter_rates doc | „Source of truth” for pricing | `MISLEADING_UI` |
| Markup as universal commercial | Applied to internal total | `FROZEN_UNTIL_REALIGNED` |
| Unused materials in registry | Accidental cost inclusion risk | `DEAD_PIECE` |

---

## 10. Target state (Step 7I)

| Tab | Content | Label |
|-----|---------|-------|
| Material Prices | unit_cost | „Cost achiziție — intern” |
| Commercial Rules | mp/ml/buc/set | „Reguli ofertă client” |
| Internal Cost Rules | Non-hourly ops | „Cost intern estimativ” |
| Capacity / Effort | Time thresholds | „Capacitate — nu preț client” |
| Analytics | Historical | „Referință post-job” |

**UI rule:** Never label `rate_per_hour` as „tarif client pe oră”.

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Single „calculate quote” button merging all tabs |
| Registry edit to unblock quote without owner commercial design |
| Material unit_cost displayed as client mp price without rule |
| New per_hour commercial rules |
| Automatic registry → quote without snapshot freeze |
| Pricing Registry data edits as Step 7E.2 substitute |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Tab separation | UI + API namespaces distinct |
| Classifications | Every entry tagged |
| Volumetric rules | Mapped commercial vs internal |
| WC relabeled | No client hourly implication |
| Template material map | Per-template used/unused list (doc 13) |
