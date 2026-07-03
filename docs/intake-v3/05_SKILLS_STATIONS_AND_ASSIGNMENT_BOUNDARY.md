# Skills, Stations and Assignment Boundary

**Regulă centrală:**

```text
Template-ul definește operații, skill-uri și stații.
Template-ul NU hardcodează persoane.
Alocarea către persoane reale se face ulterior în Execution Planning / Scheduling.
```

---

## Skill-uri conceptuale

| Skill code | Operații tipice |
|------------|-----------------|
| `graphic_design` | verificare grafică, vectorizare |
| `vector_preflight` | preflight SVG, layer review |
| `cnc_file_preparation` | fișiere debitare față/spate |
| `return_forming_file_preparation` | traseu modelare cant |
| `cnc_router_operation` | debitare CNC |
| `return_forming_machine_operation` | modelare cant |
| `vinyl_application_workbench` | colantare cant la banc |
| `letter_assembly` | lipire cant, asamblare pe Forex |
| `led_installation` | montaj module LED |
| `electrical_wiring_basic` | cablare LED, test aprindere |
| `face_vinyl_application` | colantare finală fețe |
| `packing_preparation` | infoliere stretch, colet |

---

## Stații conceptuale

| Station code | Descriere |
|--------------|-----------|
| `graphics_workstation` | grafică / vector |
| `cnc_preparation_station` | pregătire fișiere |
| `cnc_router` | debitare |
| `return_forming_machine` | modelare cant |
| `workbench` | colantare cant, lucrări manuale |
| `assembly_bench` | lipire, asamblare |
| `electrical_bench` | LED, cablare |
| `packing_area` | infoliere, colet |

---

## Persoane — non-binding

Florin, Călin, Octavian, Goghi, Cristi sunt **exemple operaționale curente** în atelier.

- Azi Florin poate fi bifat pentru CNC / pregătire fișiere / modelare cant.
- Mâine alt operator cu skill eligibil poate fi asignat.
- Template-ul și Operation Catalog referă **skill + station**, nu `employee_id`.

Asignarea reală: Execution Planning / Scheduling / Employee Mobile assignment — **după** Order și plan.

---

## Ce urmează

- Operation Catalog: `templates/TPL-VOLUMETRIC-LETTERS/05_OPERATION_CATALOG.md`
- Decizii: [07_DECISIONS_LOG.md](./07_DECISIONS_LOG.md)
