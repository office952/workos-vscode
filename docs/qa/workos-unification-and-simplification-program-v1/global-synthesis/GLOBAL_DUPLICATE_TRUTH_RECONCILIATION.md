# Global duplicate-truth reconciliation

Do not delete a page because two UIs show similar numbers.

| ID | SOURCE_A | SOURCE_B | FINAL_CLASS | CANONICAL_OWNER | TARGET_DISPOSITION |
|----|----------|----------|-------------|-----------------|-------------------|
| D-IR-IV6 | Cereri IR code | V6 header IV6 | VALID_SEPARATE_TRUTHS | both real | display policy; one primary id |
| D-EUR-RON | V6/quotes EUR | orders/clients RON | DISPLAY_DUPLICATE | backend money | label projections |
| D-CLIENT-19 | registry 1 entity | 19 activity cards | VALID_SEPARATE_TRUTHS | clients entity | clarify list vs registry |
| D-FLUX-PS | Lucrări Produse | `/product-system` | SAME_TRUTH_DIFFERENT_PROJECTION | Product System | remove Produse from FLUX |
| D-QUOTE-CLIENT | quote client text | `/clients` | COMPATIBILITY_DUPLICATE | clients | later edge; no invented link |
| D-V6-SNAPSHOT | V6 preview rail | Quote/Order snapshot | VALID_SEPARATE_TRUTHS | snapshot sold | label preview vs frozen |
| D-PRICE-REG-SNAP | pricing registry | order snapshot | VALID_SEPARATE_TRUTHS | snapshot sold | keep registry |
| D-REPORTS-SNAP | `/reports` totals | frozen snapshot | SAME_TRUTH_DIFFERENT_PROJECTION | snapshot sold | label reports live |
| D-ATELIER-OP | Atelier | `/operator` | SAME_TRUTH_DIFFERENT_PROJECTION | execution tasks | monitor vs action |
| D-OP-TABLET | `/operator` | `/tablet` | SAME_TRUTH_DIFFERENT_PROJECTION | /operator/tasks | keep compat layouts |
| D-OP-MOBILE | desktop action | employee-app-v2 | SAME_TRUTH_DIFFERENT_PROJECTION | task API | specialized mobile |
| D-92400-973024 | Atelier ORD-92400 | IV6/973024 | FALSE_POSITIVE | different work | retracted W3-C1/C4 |
| D-ASSIGN-LABEL | assigned · Neatribuit | employee assigned | FALSE_POSITIVE | frontend composition | retracted W3-C3 |
| D-12-9 | unregistered systems | Level-1 map | FALSE_POSITIVE | none | retracted W4-U12 |
| D-PD-HOME | /modules PD route | Product System | SAME_TRUTH_DIFFERENT_PROJECTION | PD compiler (no page) | do not invent page |
| D-GOV-CATALOG | governance products tab | live `/product-system` | DISPLAY_DUPLICATE | live catalog | mark stale tab |
| D-EMP-RECORDS | `/employees` names | Evidență HR | SAME_TRUTH_DIFFERENT_PROJECTION | employee master | LABEL_DEMO dossier |
| D-ADV-DEMO | profile avans demo | `/employee-advances` | DISPLAY_DUPLICATE | advances ledger | keep DEMO copy |
| D-SUPPLIER | Colaboratori | Inventory Furnizori | SAME_TRUTH_DIFFERENT_PROJECTION | suppliers API | keep both until Owner |
| D-UNIT-REG | inventory unit_cost | pricing registry | VALID_SEPARATE_TRUTHS | registry for rates | display vs rate |
| D-LABOR-3 | employee cost / CostEngine / pricing rates | — | VALID_SEPARATE_TRUTHS | each owner | keep labeled |
| D-UTIL-RUN | utilaje util% | MachineRun | VALID_SEPARATE_TRUTHS | MachineRun occupancy | honesty on catalog |
| D-PAY-ADV-COST | payment / advance / labor | — | VALID_SEPARATE_TRUTHS | each | never merge writes |
| D-ATT-SESS | pontaj | employee session | VALID_SEPARATE_TRUTHS | each | never merge |
| D-STATUS-VOCAB | executionTask / mobile / MachineRun / schedule / eligibility | — | VALID_SEPARATE_TRUTHS | each grain | W3-C5 KEEP; do not unify |

```text
TRUE_DUPLICATE_TRUTH_COUNT = 0
SAME_TRUTH_DIFFERENT_PROJECTION_COUNT = 8
VALID_SEPARATE_TRUTHS_COUNT = 11
DISPLAY_DUPLICATE_COUNT = 3
COMPATIBILITY_DUPLICATE_COUNT = 1
FALSE_POSITIVE_DUPLICATE_COUNT = 3
```
