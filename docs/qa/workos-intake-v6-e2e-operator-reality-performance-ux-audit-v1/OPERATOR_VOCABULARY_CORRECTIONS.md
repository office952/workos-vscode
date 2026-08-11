# OPERATOR_VOCABULARY_CORRECTIONS

No implementation in this GO — corrections proposed only.

| Current label | Problem | Proposed |
|---------------|---------|----------|
| `Fără finisaj — plexiglas brut` | Conflates finish absence with substrate material | Finish: **Fără finisaj**. Material (separate): canonical registry name e.g. **Plexiglas 3 mm alb opal** |
| `Oracal 651 · 60 mm` on cant | Mixes film series with return depth | Cant finish: **Oracal (cant)** + depth field **60 mm** separately |
| `CE BLOCHEAZĂ — Tarife lipsă` beside live Ofertă gross | Sounds like offer is invalid while gross shown | Split: **Ofertă client** vs **Cost intern / linii incomplete** |
| `Estimări pe produs` near Ofertă | Ambiguous vs official total | **Subtotaluri produs (compoziție)** vs **Ofertă client** |
| Technical SVG ids (`Litere_x0020_…`) | Engineering leakage | Operator label only; technical id in diagnostic |
| `Detalii tehnice despre finisaj — sursă de adevăr` | Primary chrome for internal mapping | Move under diagnostic; never primary |
| Confirm “Finisaje confirmate” while group.confirmed false | Checklist honesty drift | Align checklist with per-group commercial confirm |

## Principle

**Material** = registry substrate identity  
**Finish** = surface treatment (none / Oracal series / print / RAL / wrap)  
Never encode material inside finish option text.
