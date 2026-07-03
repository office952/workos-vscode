# 2026-07-03 Intake V6 Post-Write Human Summary Cleanup

## Context

Micro-slice anterior a adaugat CTA-ul Intake V6 `Creeaza oferta pretuita`, care foloseste endpoint-ul existent:

```txt
POST /api/v1/intake-v6/workspaces/{workspace_id}/handoff-to-offer
```

Problema ramasa: dupa priced write, `quote.notes.human_summary` putea pastra textul initial de draft, de tip preview / totaluri nescrise / draft intern. Acest text devine inconsistent dupa ce quote-ul are status `priced` si totalurile comerciale V6 sunt scrise pe oferta.

## Schimbare

Am actualizat `backend/services/intake_v6_priced_quote_write_service.py` ca, in momentul write success, sa inlocuiasca `notes.human_summary` cu un sumar priced explicit:

```txt
Oferta pretuita din Intake V6 workspace {workspace_code}. Totalurile comerciale V6 au fost scrise pe oferta ca pret comercial final. Oferta ramane in revizie interna pana la aprobarea/trimiterea catre client. Nu a fost creata comanda, executie sau miscare de stoc.
```

Fallback pentru `{workspace_code}`: daca dry-run nu furnizeaza codul, se foloseste `workspace_id`.

## Boundary

Nu am modificat:

- pricing formula;
- statusuri;
- flow UI;
- layout UI;
- DB schema;
- migrations;
- seed;
- QuoteWizard;
- flow generic/manual QuoteWizard;
- snapshot creation;
- order creation;
- execution plan;
- inventory;
- ProductAggregate;
- Task Graph;
- Employee Mobile.

Nu am rescris quote-uri vechi si nu am facut cleanup DB global.

## Test

Am actualizat testul backend de write success pentru a cere noul `human_summary` si pentru a confirma ca textul nu contine `QuoteWizard`, `preview` sau `nu au fost inca scrise`.

Comanda:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_priced_quote_write.py -q
```

Rezultat:

```txt
20 passed, 3 warnings
```

## Note

Quote-ul runtime existent `Q-V6-IV6-CA9DA36C-1783037396` ramane nerescris intentionat, conform regulii de a nu face cleanup DB global. Schimbarea se aplica la urmatorul V6 priced write / handoff-to-offer reusit.
