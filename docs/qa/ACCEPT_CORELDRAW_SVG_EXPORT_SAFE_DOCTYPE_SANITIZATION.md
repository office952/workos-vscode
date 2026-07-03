# ACCEPT_CORELDRAW_SVG_EXPORT_SAFE_DOCTYPE_SANITIZATION

## Problema reală

Ownerul exportă SVG din **CorelDRAW**. Exportul standard include declarație `DOCTYPE` W3C SVG 1.1.

Fișier real: `blueprints/volumetric-letter-svg-test/litere-volumetrice.svg`

Înainte de fix, upload-ul reușea parțial (raw analysis), dar **`path_geometry_summary`** eșua cu `xml_unsafe_construct` — operatorul nu putea continua Geometry → Lighting fără edit manual al fișierului.

**Nu cerem ownerului să editeze manual SVG-ul** — CorelDRAW DOCTYPE este fluxul normal de lucru în producție.

## Strategia sigură

| Principiu | Decizie |
|-----------|---------|
| Parser | Rămâne `xml.etree.ElementTree` + guard pre-parse |
| Securitate | Fail-closed pe `<!ENTITY>`, subset DTD intern, XXE |
| DOCTYPE standard Corel | Eliminat **doar** din copia de parse geometry |
| Raw SVG stocat | **Neschimbat** — sanitizare doar în memorie la parse |
| Lighting / CostEngine | **Neatinse** |

Helper canonical:

- `prepare_svg_text_for_safe_geometry_parsing()` — pipeline geometry
- `sanitize_svg_for_safe_geometry_parse()` — alias explicit CorelDRAW

## Ce acceptăm

- DOCTYPE SVG W3C standard (single-line sau multiline fără `[`)
- SVG CorelDRAW fără `<!ENTITY>`
- Fixture existent `volumetric-multilayer.svg`

## Ce blocăm

- `<!ENTITY ...>` → `svg_unsafe_entity_declaration`
- Subset DTD intern (`<!DOCTYPE ... [`) → `svg_unsafe_dtd_declaration`
- XXE / external entity patterns
- Orice DTD rămas după sanitizare

Mesaj operator (RO):

> SVG-ul conține declarații XML nesigure. Exportă SVG fără entități/DTD sau contactează administratorul.

## Implementare

### Backend

- `svg_sanitization_service.py` — sanitizare + erori operator-friendly
- `build_path_geometry_summary_from_svg_text()` — folosește text sanitizat
- `attach_svg_raw_analysis_to_workspace()` — path geometry la upload

### Frontend

- `pathGeometryUploadNotice.ts` — mapare erori tehnice → mesaj operator
- `IntakeV3OperatorSvgLayersTab` — afișează eroarea path geometry după upload
- Fără mesaj alarmist când DOCTYPE a fost sanitizat cu succes

## Teste de securitate

| Test | Rezultat |
|------|----------|
| SVG fără DOCTYPE | Parse OK |
| DOCTYPE standard | Sanitizat, parse OK |
| DOCTYPE multiline | Sanitizat, parse OK |
| `<!ENTITY>` | Blocat |
| XXE pattern | Blocat |
| `litere-volumetrice.svg` | `parse_status=parsed`, fără `xml_unsafe_construct` |
| `volumetric-multilayer.svg` | Parse OK |

## Test Corel / owner

Fișier: `litere-volumetrice.svg` (blueprint existent, necomis ca fixture nou)

| | Înainte | După |
|-|--------|------|
| `path_geometry_summary.parse_status` | `failed` | **`parsed`** |
| `error_code` | `xml_unsafe_construct` | **null** |
| `doctype_removed_for_safe_parse` | — | **true** |
| Path layers | 0 | **2** (`fata_x0020_plexiglas`, `autocolant`) |
| `perimeter_mm_approx` | — | **~459.89 mm** |

Raw analysis: groups Spate, sanfren, volum, fata_x0020_plexiglas, autocolant (unchanged).

## Comenzi test

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest `
  tests/test_intake_v3_path_geometry_svg_sanitization.py `
  tests/test_svg_sanitization.py `
  tests/test_intake_v3_lighting_plan.py `
  tests/test_intake_v3_operator_workspace_e2e_hardening.py -q

cd ..\frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV3/pathGeometryUploadNotice.test.ts
```

## Boundary confirmations

- No CostEngine / Inventory / StockMovement / ExecutionTask / ExecutionPlan / PO / SupplierOrder
- No Lighting / PSU / reserve changes
- No Atoms recomposition
- No unsafe XML parser / no XXE / no entity expansion
- No DB manual edit / no push
- `tmp/` și `backend/dev.db` necomise
- Owner SVG necomis ca fixture nou

## Ce rămâne

1. Runtime smoke: file-drop upload `litere-volumetrice.svg` în Operator Workspace → layer roles → Lighting
2. Path geometry pentru straturi `<polygon>`-only (Spate, sanfren) — scope separat
3. Unificare sanitizare în `analyze_svg_content()` (raw analysis path) — optional hardening
4. Commit controlat când owner aprobă

## Verdict

**PASS — CorelDRAW SVG DOCTYPE safely sanitized and parsed**
