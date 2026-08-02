# Role surface matrix

| Surface | Admin | Manager | Operator | Dev Mode |
|---|---|---|---|---|
| Produse și șabloane | Administer permitted template surfaces | Read permitted workspace surfaces | Read-only when existing authorization allows | Preserved; no change to `VITE_ENABLE_DEV_AUTH`. |
| Registru prețuri | Existing registry actions | Existing permitted read/actions | Existing permitted read | Preserved. |
| Utilaje și capacitate | Existing registry editor when API permits | Read capacity/maintenance | Read operational context | Preserved. |
| Setări administrative | Existing settings and integration actions | Existing permitted views | No new authority | Preserved. |
| Guvernanță | Read-only policy/ownership | Read-only policy/ownership | Read-only where visible | Preserved. |

This track changes presentation only. It adds no role, API, persistence, or authorization behavior.
