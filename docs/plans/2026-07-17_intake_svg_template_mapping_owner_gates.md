# Owner gates — Intake SVG ↔ Product System mapping

| Gate | Optiuni | Recomandare | Motiv |
|------|---------|-------------|-------|
| Ce selectează operatorul | layer / element / grup / contur | **Layer și/sau closed contour** (unitate geometrică) | Layer = litere/logo azi; chenarul ACP e contur (polygon), nu rol de layer owner |
| Ce reprezintă alegerea | rol SVG / componentă / template | **Asociere la componentă** (după rol geometric opțional) | Template-ul de produs e deja ales; layer role ≠ Product Template |
| Sursa opțiunilor | Intake / registry / Product System | **Product System** (componente active) | Evită hardcode FE; scalează Forex/metal/totem |
| Label pentru ACP | Vector fundal / Contur suport / Panou ACP | **Contur suport** → confirmă **Panou Alucobond casetat** | Rol geometric ≠ material; componenta e PS |
| Activare componentă | înainte / după selecție | **Înainte sau odată cu asocierea** (optional support on) | Inactive isolation: zero casing dacă suport inactiv |
| Multiple elemente | permis / interzis | **Permis pentru litere** (mai multe layere→aceeași componentă); **V1 un contur suport** | Litere multi-layer există; un panou V1 |
| Multiple suporturi | permis / V1 un singur suport | **V1 un singur suport** | Contract existent XOR metal/Alucobond |
| Closed-contour integration | același flow / flow separat | **Același flow** (unificare) | Dual SoT acum: `TPL-BOND-CASETAT` vs ACM boxed |
| ProductDefinition mapping | component instance / finish_setup legacy | **Component instance + mounting_solution typed**; fix schema selection | `svg_support_selection` e dropat de FinishSetup |
| Product System first | da / nu | **Da** | Contractul lipsă e expunerea PS, nu doar UI Intake |

## Configurație finală recomandată (o singură)

```text
Product Template: TPL-VOLUMETRIC-LETTERS_v2
→ PS expune componente SVG-bindable (litere, logo opțional, suport opțional)
→ Operator alege unitate geometrică (layer / closed contour)
→ Asociază componentei
→ Dacă componenta = Panou Alucobond casetat → casing config
→ ProductDefinition păstrează instanțele + geometry refs
→ Un singur flow Step 1 (fără panou Alucobond paralel)
```

## Decizii care blochează implementarea

1. Acceptă unificarea closed-contour în assignment-ul de componente?
2. Acceptă pensionarea `TPL-BOND-CASETAT` ca țintă de composition?
3. Acceptă GO separat pentru FinishSetup `svg_support_selection` persistence?
