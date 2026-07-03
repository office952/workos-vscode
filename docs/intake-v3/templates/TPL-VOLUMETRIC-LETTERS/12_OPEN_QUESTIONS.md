# TPL-VOLUMETRIC-LETTERS — Open Questions

---

## Suport și montaj

| # | Întrebare | Status |
|---|-----------|--------|
| Q1 | Model complet pentru bare / ACM / casetă / structură comună? | `OWNER_ANALYSIS_REQUIRED` |
| Q2 | Când apare `electrical_source_mounting_on_support` vs colet? | pending P1 |

---

## Granularitate taskuri

| # | Întrebare |
|---|-----------|
| Q3 | Cât de granular spargem taskurile reale în ExecutionPlan vs checklist în Mobile? |
| Q4 | `return_painting_after_assembly` — task unic sau sub-pași în checklist? |
| Q5 | Colantare cant + modelare — mereu secvențial strict sau excepții atelier? |

---

## ProductSystem / registry

| # | Întrebare |
|---|-----------|
| Q6 | Operation Catalog devine entitate first-class în ProductSystem sau rămâne docs + service? |
| Q7 | Legătura template operations_json vs Operation Catalog V3 — migrare sau paralel? |

---

## Intake V3 product

| # | Întrebare |
|---|-----------|
| Q8 | Custom pe literă (`letter_custom`) în pilot sau doar all/group? |
| Q9 | Când activăm UI `/intake-v3` — după care adapter? |
| Q10 | Migrare intake V2 existente — da/nu/cum? |
| Q11 | Persistență `intake_schema_version=3` în același `intake_requests`? |

---

## Planning / HR

| # | Întrebare |
|---|-----------|
| Q12 | Cum conectăm skill matrix / fișă post cu planning real și eligibilitate? |
| Q13 | Stațiile devin entități WorkCenter registry sau rămân coduri documentate? |

---

## STOP rule

Întrebările de mai sus nu primesc răspuns inventat în implementare. Adaugă decizie în [../../../07_DECISIONS_LOG.md](../../../07_DECISIONS_LOG.md) după owner review.
