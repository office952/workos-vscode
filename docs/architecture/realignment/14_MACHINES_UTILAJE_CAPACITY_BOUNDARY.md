# Machines / Utilaje — Capacity Boundary

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Related:** `OPERATIONAL_RESOURCE_MAPPING_ARCHITECTURE.md`

---

## 1. Rolul sistemului

Machines/Utilaje deține **utilaje, capabilități, limite, disponibilitate, mentenanță, capacitate, risc defect** — influențând fezabilitate, timp estimativ, capacitate, risc și cost intern — **nu** prețul comercial client.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Utilaje** | CNC, laser, forming, painting booths, etc. |
| **Capabilități** | What each machine can do |
| **Limite** | Size, thickness, material types |
| **Disponibilitate** | Calendar, maintenance windows |
| **Mentenanță** | Downtime scheduling |
| **Capacitate** | Load planning |
| **Risc defect** | Machine health signals |
| **Workcenter mapping** | Machine ↔ workcenter association |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Preț comercial client |
| Formula universală de ofertă |
| CommercialPriceProposal |
| Client hourly tariff |
| HR payroll |
| ProductDefinition structure |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Admin registry | Machine definitions |
| Maintenance logs | **UNKNOWN** detail level |
| ExecutionPlan | Assignment requests |
| ProductAggregate | Required workcenters / machine_type |
| Operational registry | Partial wiring |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Feasibility flags | Intake/Definition gates — **NEEDS_OWNER_DECISION** |
| Capacity warnings | EstimatedInternalCost sanity / planning |
| Machine assignment | ExecutionPlan |
| Utilization stats | Analytics, ProfitabilityAnalysis |
| Estimated time hints | Planning — **not commercial price** |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Machine capabilities | **Registry truth** |
| Workcenter rates | Pricing Registry — **reclassified internal** |
| Commercial CNC lei/ml | Commercial Price Rules — **NOT** machine registry |
| Real machine time | ExecutionActuals |

---

## 7. Conexiuni cu celelalte sisteme

```
ProductAggregate (operation → workcenter → machine_type)
    ↓
Machines/Utilaje (feasibility + capacity)
    ↓
ExecutionPlan (assignment)
    ↓
ExecutionActuals (actual machine time)
    ↓
ProfitabilityAnalysis (efficiency learning)

✗ CommercialPriceProposal — machines influence rules indirectly (material/thickness) not hourly
```

| Sistem | Relație |
|--------|---------|
| Pricing Registry WC rates | Named by workcenter — separate from machine entity |
| Cost Engine | machine_rate in settings — **FROZEN** commercial risk |
| Intake | Partial machine_type refs — **partial** audit |

---

## 8. Reguli owner obligatorii

1. CNC commercial = lei/ml by material/thickness/bevel — **not** machine hourly to client.
2. Machine influence on internal cost = optional capacity factor — **NEEDS_OWNER_DECISION**.
3. Bevel/sanfren requires CNC not laser — owner rule in costing audit.
4. Utilaje ≠ tarif client pe oră in UI labels.

---

## 9. Riscuri actuale din audit

| Risc | Detaliu | Tag |
|------|---------|-----|
| machine_rate_ron_per_hour settings | Hourly fallback | `FROZEN_UNTIL_REALIGNED` |
| operational_registry not wired intake | Skill/eligibility gap | Partial |
| WC rate conflated with machine | Naming | `MISLEADING_UI` |
| Capacity not blocking commercial | Target — warnings only | OK |

---

## 10. Target state

| Aspect | Țintă |
|--------|-------|
| Machine registry complete | Linked to workcenters |
| Capacity warnings | Non-blocking commercial |
| Assignment in ExecutionPlan | Machine id on task |
| Analytics | ml/min per machine post-job |
| Clear labels | Capacity ≠ client price |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Machine hourly rate → client quote line |
| Block commercial offer on machine maintenance alone |
| Machine registry as Pricing hub |
| Confuse workcenter rate_per_hour with client tariff |
| Auto-commercial price from machine calendar |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Machine ↔ WC map | Documented |
| No commercial hourly from machines | Policy clean |
| ExecutionPlan assignment | Machine traceable |
| Capacity warnings separated | From commercial blockers |
| Post-job analytics | Machine efficiency in ProfitabilityAnalysis |
