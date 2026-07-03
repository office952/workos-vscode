# TPL-VOLUMETRIC-LETTERS — Shared Support (Pending Model)

**Status:** `OWNER_ANALYSIS_REQUIRED`  
**Boundary:** acest document nu definește logică finală

---

## Ce înseamnă suport comun

Literele sau ansamblul sunt montate în atelier pe o structură comună:

- bare metalice;
- panou Dibond / ACM / Alucobond;
- casetă;
- structură de montaj comună pe spate.

---

## Ce poate deveni diferit față de fără suport comun

| Aspect | Posibil diferit |
|--------|-----------------|
| Confecționare suport | operație nouă |
| Montaj litere pe suport | nu doar pe Forex individual |
| Cablare / surse | task `electrical_source_mounting` pe suport |
| Test ansamblu | verificare electrică la nivel suport |
| Ambalare | ansamblu complet, nu litere individuale în colet |
| Surse | montate pe suport în atelier, nu în colet |
| Transport / montaj | logică diferită |

---

## Operații candidate (nevalidate)

- `shared_support_fabrication`
- `letters_mount_on_shared_support`
- `electrical_source_mounting_on_support`
- `assembly_integration_test`
- `shared_support_packaging`

**Nu activa** aceste coduri în runtime până la decizie owner și build dedicat.

---

## Legături

- Fără suport comun: [07_NO_SHARED_SUPPORT_TASK_LOGIC.md](./07_NO_SHARED_SUPPORT_TASK_LOGIC.md)
- Decisions: [../../../07_DECISIONS_LOG.md](../../../07_DECISIONS_LOG.md) (P1)
