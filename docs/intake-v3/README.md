# Intake V3 — Documentation Dossier

**Status:** documentation foundation  
**Branch reference:** `local/integration-pr4-plus-svg-path`  
**Boundary:** docs only — no UI, no runtime, no DB migration

---

## Ce este acest dossier

Packet oficial de documentație pentru **Intake V3** în WorkOS / ProductSystem. Organizează două straturi:

1. **Work Intake general** — ce înseamnă intake-ul, ce colectează, ce validează, ce nu face.
2. **Template-specific** — model operațional pentru `TPL-VOLUMETRIC-LETTERS`.

Intake V3 este **greenfield**: nu refactorizează V1/V2. Atoms V6 este **design reference**, nu sursă de implementare. Primul build real a fost **Architecture Contracts** (`959d53c`).

---

## Documente globale

| Document | Rol |
|----------|-----|
| [00_STATUS.md](./00_STATUS.md) | Stare curentă, ce există / ce lipsește |
| [01_WORK_INTAKE_GENERAL_MODEL.md](./01_WORK_INTAKE_GENERAL_MODEL.md) | Definiție Work Intake |
| [02_WORK_INTAKE_LIFECYCLE.md](./02_WORK_INTAKE_LIFECYCLE.md) | Lifecycle conceptual |
| [03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md](./03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md) | Boundary comercial + producție |
| [04_READINESS_AND_BLOCKERS_MODEL.md](./04_READINESS_AND_BLOCKERS_MODEL.md) | ReadinessReport |
| [05_SKILLS_STATIONS_AND_ASSIGNMENT_BOUNDARY.md](./05_SKILLS_STATIONS_AND_ASSIGNMENT_BOUNDARY.md) | Skill-uri, stații, fără persoane hardcodate |
| [06_BUILD_ROADMAP.md](./06_BUILD_ROADMAP.md) | Roadmap builduri |
| [07_DECISIONS_LOG.md](./07_DECISIONS_LOG.md) | Decizii luate și pending |

---

## Template pilot

| Document | Rol |
|----------|-----|
| [templates/TPL-VOLUMETRIC-LETTERS/README.md](./templates/TPL-VOLUMETRIC-LETTERS/README.md) | Index template volumetric |

---

## Legături externe (repo)

| Artifact | Path |
|----------|------|
| Architecture contracts | [../architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md](../architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md) |
| QA contracts build | [../qa/BUILD_INTAKE_V3_ARCHITECTURE_CONTRACTS.md](../qa/BUILD_INTAKE_V3_ARCHITECTURE_CONTRACTS.md) |
| Backend contracts | `backend/schemas/intake_v3.py` |
| Readiness skeleton | `backend/services/intake_v3_readiness_service.py` |
| Frontend types | `frontend/src/lib/intakeV3/contracts.ts` |

---

## Reguli de menținere

- Un document = un scop clar; fără monolituri.
- Fiecare document spune ce **este**, ce **nu este**, ce **urmează**.
- Logica operațională = catalog condiționat, nu listă statică de pași.
- Dacă producția e neclară → STOP, owner decision.
