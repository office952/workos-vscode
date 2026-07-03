# Color registry import — format & sources

## Status

**Full palette is active** in runtime registry (generated 2026-06-08):

| System | Count | Source |
|--------|-------|--------|
| RAL Classic | 213 | `sources/ral_standard.csv` |
| Oracal 651 | 80 | `sources/oracal651-orafol.txt` (ORAFOL) |
| Oracal 8500 | 55 | `sources/oracal8500-orafol.txt` (ORAFOL) |

Regenerate TS from sources:

```bash
cd frontend
npm run generate:color-registry
```

Outputs: `../ralColors.ts`, `../oracal651.ts`, `../oracal8500.ts`, and `sources/color-registry-full.csv`.

## Known external references (not imported)

| System | Reference | Status |
|--------|-----------|--------|
| Oracal 651 | folii-adezive.ro — Oracal 651 Intermediate Cal | Not in repo — manual validation required before import |
| Oracal 8500 | folii-adezive.ro — Oracal 8500 Translucent Cal | Not in repo — manual validation required before import |
| RAL Classic | Industry RAL fan decks / supplier PDFs | No machine-readable file in repo |

## Import workflow (when validated CSV exists)

1. Place file here: `import/validated/color-registry.csv` (gitignored until approved)
2. Validate (does not write TS automatically):

   ```bash
   cd frontend
   node scripts/validate-color-registry-import.mjs src/lib/colorRegistry/import/color-registry-import.template.csv
   ```

3. Review validator output — zero errors required
4. Separate build: generate or hand-merge `ralColors.ts` / `oracal651.ts` / `oracal8500.ts` from validated CSV

## CSV format

See `color-registry-import.template.csv` for header and example rows.

Required columns:

```txt
system,brand,series,code,name,romanianName,previewHex,finish,usageScope,translucent,active,source,notes
```

Rules summary:

- `system`: `RAL` or `ORACAL`
- Oracal: `brand=Oracal`, `series=651|8500`
- RAL: no `series`, no `brand`
- `8500`: `translucent=true`
- `651`: `translucent=false`
- `previewHex`: `#RRGGBB` (approximate for RAL)
- `usageScope`: semicolon-separated scopes
- `source`: required non-empty provenance string
- Unique key: `system + series + code`

Validator: `src/lib/colorRegistry/import/validateColorRegistryImport.mjs`
