# Route disposition

| Route | U3 disposition | Primary operator question | Boundary |
|---|---|---|---|
| `/product-system` | Improved | Ce produs și șablon structurez? | Șablonul descrie structură; nu confirmă Product Truth și nu stabilește rate catalog. |
| `/pricing` | Improved | Ce sursă de cost/regulă susține această rețetă? | Materiale, reguli ofertă, cost intern, capacitate și legacy rămân distincte. |
| `/utilaje` | Improved | Ce capacitate și mentenanță are utilajul? | Workcenter/utilaj = fezabilitate; nu tarif client. |
| `/settings` | Improved | Ce configurație administrativă pot gestiona? | Configurație, integrare și cost intern; nu politici de guvernanță. |
| `/governance` | Improved | Cine deține regula și ce gate se aplică? | Read-only policy/ownership; nu configurație. |

No router ownership changed. App shell, route registration, AuthContext, and Dev Mode gate remain untouched.
