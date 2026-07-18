# ACP / ACM / Dibond / Alucobond — Terminology Map

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_FINALIZE_BLUEPRINT_AUDIT_AND_AUDIT_ACP_COMPOSABLE_FACE_SYSTEM` |
| Mode | Audit only — no renames |

---

## Map

| Termen | Tip | Unde apare | Înseamnă | Authority | Alias legitim | Conflict |
|--------|-----|------------|----------|-----------|---------------|----------|
| **ACP** | Shorthand material / produs | UI „Panou ACP casetat”, family `panouri_acp_iluminate`, materials `MAT-ACP-*` | Aluminium Composite Panel (shop language) | Split — UI vs codes | ACM, Dibond, Alucobond, Bond | `MAT-ACP-FATA-LITERE` = plexi față litere, **nu** panou ACM |
| **ACM** | Familie / prefix template | `TPL-ACM-*`, `MAT-ACM-BOND-*`, inventory | Same physical family as ACP/Dibond | Product System templates + material registry | ACP, Dibond, Alucobond | UI says ACP; codes say ACM |
| **Alucobond** | Brand / label owner | Contour `ALUCOBOND_CASED_PANEL`, „Panou Alucobond casetat” | Closed-contour cased panel role | Contour confirm → binding `SUPPORT_CONTOUR` → `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | ACP casetat, ACM boxed | Contour role ≠ geometry role ≠ layer role |
| **Dibond** | Brand / inventory | Inventory governance, layer synonyms | Alias for ACM stock | Inventory naming | ACM, Alucobond, Bond | Analyzer may map name → `support_panel` only |
| **bond** | Ambiguous | Layer `backing` synonyms, nesting „Bond return”, `MAT-ACM-BOND-*` | Sometimes panel, sometimes letter backing | Context-dependent | — | High confusion |
| **aluminiu compozit** | RO label | ProductSystem viz copy | Front panel material description | Viz only | ACP | Not a template code |
| **composite panel** | Generic EN | Docs / materials | Same family | — | ACP/ACM | Unused as identity |
| **boxed / casetat / cassette panel** | Construction mode | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`, folds | Folded returns → cassette depth | ACM boxed template + SVG casing | cased, `TPL-ACM-CASSETTED-PANEL` | Boxed mounting ≠ full illuminated cabinet |
| **mounting support** | Product / commercial mix | `mounting_solution`, Contur suport | Support child under letters **or** standalone | Now **product component** independent of commercial `mounting_scope` | Contur suport | Historically mislabeled as prep |
| **luminous panel / sign cabinet** | Product family (legacy path) | `TPL-ACP-LIGHT-ROUTED`, family panouri ACP iluminate | Backlit routed ACP + plexi + LED + relief | CostEngine / QuoteWizard hierarchical template | Panou ACP iluminat | Parallel to Intake V6 ACM boxed — not SVG-bindable composition |
| **Contur suport** | Geometry role (owner) | `SUPPORT_CONTOUR` | Outer closed contour for support panel | PS SVG binding contract | `support_panel`, `ALUCOBOND_CASED_PANEL` | Three vocabularies |
| **face_mode / face_treatment / visual_zones** | **Absent** | No runtime SoT | Owner mixed-face concept | — | — | **Not modeled** |

---

## Clarifications (no rename)

1. **Categorie tehnică:** aluminium composite cassette / panel family.
2. **Brand:** Alucobond / Dibond — shop synonyms for ACM/ACP stock.
3. **Label owner-facing:** prefer „Panou Alucobond casetat” / „Panou ACP casetat” in Intake; codes remain `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`.
4. **Cod intern canonic live:** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`.
5. **Duplicates:** ACM boxed vs `TPL-ACM-CASSETTED-PANEL` (candidate) vs `TPL-ACP-LIGHT-ROUTED` (illuminated legacy).
6. **Legacy aliases:** `TPL-BOND-CASETAT` — string-only, blocked for new selection.
7. **Authority conflict:** do not treat CostEngine illuminated template as Intake V6 composition SoT without explicit GO.

---

## Separation rule (owner)

```text
geometry role  ≠  component  ≠  face treatment  ≠  finish  ≠  material
```

Today the live path collapses most of these into: one `SUPPORT_CONTOUR` + global casing config + separate letter/logo product bindings.
