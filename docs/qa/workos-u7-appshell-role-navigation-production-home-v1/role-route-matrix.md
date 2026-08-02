# Role → route matrix (U7)

| Rol real | Home implicit | Secțiuni vizibile | Rute directe tipice | Admin? | Diagnostic? |
|----------|---------------|-------------------|---------------------|--------|-------------|
| operator | `/shop-floor` | Producție, Resurse | Atelier, Acțiune task, Stații, Utilaje, Inventar | Nu | Nu |
| manager | `/shop-floor` | Lucrări…Management (fără Prețuri/Avansuri/Admin) | + Ops-Graph audit, Control preview, HR, Plăți | Nu | Ops-Graph |
| sales | `/quotes` | Lucrări, Producție(Planificare), Resurse(Inventar), Relații, Management(Control/Rapoarte) | Cereri…Comenzi, Clienți | Nu | Nu |
| admin | `/dashboard` | Toate + DEV tooling (DEV auth) | + Prețuri, Avansuri, Administrare, demos | Da | Da (DEV) |
| viewer | `/dashboard` | Management: Control | Control only | Nu | Nu |

UI hide ≠ backend auth. Mutations remain API-gated.
