# PII / secrets scan — Atoms demo seed files

**Date:** 2026-08-10  
**Scope scanned:** `backend/demo/`, `backend/scripts/seed_atoms_demo_v1.py`, `scripts/demo-*.ps1`, `docs/operations/WORKOS_ATOMS_DEMO_ENVIRONMENT.md`

| Check | Result |
|-------|--------|
| Real client names | NONE — Demo Client Alpha/Beta/Gamma/Delta |
| Real employee names | NONE — Demo Operator CNC / Assembler / Finisher |
| Emails | `*@example.invalid` / `atoms-demo@example.invalid` only |
| Phone numbers | NONE |
| JWT / API keys / passwords | NONE committed; JWT secret is local-dev placeholder in scripts only |
| Owner Desktop paths | NONE in demo seed (golden fixture pack under `tests/fixtures/`) |
| Historical golden workspace mutation | NO |
| `backend/dev.db` committed | NO |
| Binary demo DB committed | NO |

```text
PII_SCAN = PASS
```
