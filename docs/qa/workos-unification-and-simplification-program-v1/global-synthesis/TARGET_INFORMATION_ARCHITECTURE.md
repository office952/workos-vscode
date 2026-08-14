# Target information architecture

Conceptual. **Do not change nav code.**

A business user should see **work**, then **people**, then **resources**, then **admin**. Not every backend subsystem.

## Proposed groups

| Group | Contains | Does not contain |
|-------|----------|------------------|
| **ACASĂ** | Role home only: sales→Oferte, operator/manager→Atelier, admin→Control (or Atelier) | Audit stacks as the only story |
| **CERERI / VÂNZĂRI** | Cereri, Intake V6 (not a sibling “Produse”), Oferte, Comenzi, optional Clienți | Product System, Documents mock |
| **PRODUCȚIE** | Atelier, Planificare, Rulări utilaj | Ops-Graph, Reality Review, FLUX Produse |
| **OAMENI** | Angajați, Pontaj, Plăți, Avansuri | Evidență HR unless labeled DEMO |
| **RESURSE** | Inventar, Utilaje, Prețuri (admin), Furnizori *or* Colaboratori as primary | MachineRun occupancy |
| **MANAGEMENT** | Rapoarte (labeled projection), Control producție | People money (moved) |
| **CONFIGURARE / ADMIN** | Product System, Setări | Everyday operator path |
| **SISTEM / AUDIT** | Harta, Guvernanță, Ops-Graph, Reality Review, operational reports, lab previews | Primary Lucrări |

## Commercial recommendation (one model)

Teach:

```text
Cerere → configurare în Intake → Ofertă → Comandă
```

**FLUX Produse leaves Lucrări.** Product System lives under Configurare. That is the single highest-value IA change in the program.

## Execution recommendation

Keep Atelier as **watch**. Keep `/operator` and `/tablet` as **compat** until Owner picks a canonical action home. Demote audit graphs from Producție.

## People / relations

Move Plăți + Avansuri under Oameni. Documents leave primary Relații until real. Clienți may stay Relații or join Vânzări — Owner decision. Colaboratori stays a projection of suppliers, not a second registry.
