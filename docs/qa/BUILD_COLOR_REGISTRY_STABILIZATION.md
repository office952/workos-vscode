# BUILD: Color Registry Stabilization — Standalone

**Date:** 2026-06-09
**Base commits:** `1f581cd`, `a005514`, `3b8ff36`
**Status:** see §11 Verdict

---

## 1. Audit inițial

### Fișiere existente (pre-build)

| Locație | Stare git | Rol |
|---------|-----------|-----|
| `frontend/src/lib/colorRegistry/**` | untracked | Registry lib, date, import pipeline |
| `frontend/src/components/workos/colorRegistry/**` | untracked | UI selector standalone |
| `frontend/scripts/generate-color-registry.mjs` | untracked | Generator TS din surse CSV/txt |
| `frontend/scripts/validate-color-registry-import.mjs` | untracked | CLI validator CSV |
| `docs/qa/BUILD_COLOR_AND_VINYL_REGISTRY_RAL_ORACAL.md` | untracked | QA vechi (WI V2 integrat) |
| `docs/qa/BUILD_COLOR_REGISTRY_FULL_PALETTE_IMPORT_PREP_AND_E2E.md` | untracked | QA vechi (import + e2e) |
| `frontend/e2e/work-intake-v2-color-registry.spec.ts` | untracked | e2e — off-limits |
| `frontend/wip/color-registry-intake/**` | nou (post-audit) | Patch helpers IntakeProductSpec |

**Tracked modified:** niciun fișere color registry în HEAD; tot pachetul era WIP untracked.

### Tipuri de culori

| Sistem | Fișier | Acoperire |
|--------|--------|-----------|
| **RAL Classic** | `ralColors.ts` | 213 culori (generat din `import/sources/ral_standard.csv`) |
| **Oracal 651** | `oracal651.ts` | 79 culori colored cast vinyl |
| **Oracal 8500** | `oracal8500.ts` | catalog translucent pentru față iluminată |
| Altele | — | none |

### Componente UI (pre-build)

| Componentă | Fișier | Note |
|------------|--------|------|
| Selector | `ColorRegistrySelect.tsx` | search, listă, swatch, filtre |
| Swatch | inline `ColorSwatch` | în selector |
| Preview | swatch HEX + label | `formatColorRegistryLabel` |
| Helperi intake | `colorRegistrySpec.ts` | **coupling IntakeProductSpec — de-scoped** |

### Teste (pre-build)

| Fișier | Acoperire |
|--------|-----------|
| `colorRegistry.test.ts` | lookup, filter, search |
| `colorRegistrySpec.test.ts` | patch intake — **de-scoped → wip** |
| `validateColorRegistryImport.test.ts` | CSV import validator |
| `ColorRegistrySelect.test.tsx` | UI selector |

### Work Intake V2 — de-scoped anterior

Commit `a005514` a eliminat din WI V2:

- import `ColorRegistrySelect`
- `colorRegistrySpec` patch helpers în production stage
- `VolumetricFinishDisplayPanel` / `volumetricFinishDisplay`

**Verificare curentă:** zero match `colorRegistry` în `workIntakeV2/**` și `workIntakeV2/lib/**`.

### Dependențe volumetric / finish display

| Fișier | Direcție | Stare |
|--------|----------|-------|
| `volumetricFinishDisplay.ts` | importă `colorRegistry` | untracked WIP, **necomis** |
| `ColorRegistrySelect.tsx` (pre-fix) | importa `workIntakeV2/shared` | **remediat** — clase locale |

### Cel mai mic build coerent

1. `colorRegistryTypes.ts` + date (`ralColors`, `oracal651`, `oracal8500`)
2. `colorRegistry.ts` — filter, search, lookup, normalize, label
3. `import/` — validator CSV + surse (portabilitate palette)
4. `ColorRegistrySelect.tsx` — UI decoupled
5. Teste lib + UI + import validator
6. **Exclude:** `colorRegistrySpec` (intake), scripts npm root, e2e, QA vechi duplicate

---

## 2. Scope

Standalone color registry infrastructure:

- tipuri, date RAL/Oracal, helperi lookup/normalizare
- componentă selector reutilizabilă
- teste unitare
- **fără** integrare Work Intake V2, volumetric preview, backend, e2e, seed

---

## 3. Fișiere incluse (commit)

```
frontend/src/lib/colorRegistry/
frontend/src/components/workos/colorRegistry/
docs/qa/BUILD_COLOR_REGISTRY_STABILIZATION.md
```

---

## 4. Registry-uri disponibile

| Registry | Cod sistem | Series | usageScope tipic |
|----------|------------|--------|------------------|
| RAL Classic | `RAL` | — | return, structure, cable_channel |
| Oracal 651 | `ORACAL` | `651` | return, face_vinyl |
| Oracal 8500 | `ORACAL` | `8500` | illuminated_face (translucent) |

---

## 5. Helperi disponibili

| Helper | Rol |
|--------|-----|
| `ALL_COLOR_REGISTRY_ITEMS` | catalog unificat |
| `filterColorRegistry` | filtru system/series/usageScope/active |
| `searchColorRegistry` | căutare text cod/nume |
| `normalizeColorRegistryCode` | strip prefixe `RAL`, `651-`, etc. |
| `findColorRegistryItem` | lookup după cod normalizat |
| `lookupColorRegistryItem` | lookup cu result `found` \| `unknown` |
| `formatColorRegistryLabel` | label UI cod + nume |

Import pipeline (lib, necomis ca script npm):

- `import/validateColorRegistryImport.mjs` — validare CSV
- `import/sources/*` — surse regenerare palette

---

## 6. Componente UI

**`ColorRegistrySelect`**

- props: `label`, `valueCode`, `filter`, `onChange`, `disabled`, `testId`, `showApproxNote`
- swatch + cod + nume + badge system/series
- notă aproximare RAL opțională
- **zero** import din `workIntakeV2/**`

---

## 7. Teste rulate

```powershell
cd frontend
npm run test -- colorRegistry
npm run typecheck
cd ..
npm run validate:frontend
```

(Rezultate în §10 output final.)

---

## 8. Clean checkout safety

Verificări post-staging:

```powershell
git diff --cached --name-only
git diff --cached --check
git grep "workIntakeV2" frontend/src/lib/colorRegistry frontend/src/components/workos/colorRegistry
git grep "volumetricFinishDisplay" frontend/src/lib/colorRegistry frontend/src/components/workos/colorRegistry
git grep "VolumetricFinishDisplayPanel" frontend/src/lib/colorRegistry frontend/src/components/workos/colorRegistry
```

HEAD + staged trebuie să compileze fără fișiere untracked din alte zone WIP.

---

## 9. Boundary explicit

| Zone | Inclus |
|------|--------|
| Work Intake V2 | **NU** |
| volumetric preview / finish display | **NU** |
| ProductSystem | **NU** |
| Pricing / CostEngine | **NU** |
| backend | **NU** |
| e2e / seed | **NU** |
| App.tsx | **NU** |
| Quotes / ANAF / clients | **NU** |
| `colorRegistrySpec` (intake patches) | **NU** — mutat în `frontend/wip/color-registry-intake/` |

---

## 10. Riscuri rămase

1. **Preview HEX RAL** — aproximativ; notă UI disponibilă dar nu obligatorie.
2. **Integrare WI V2** — patch helpers în wip; build viitor separat.
3. **`volumetricFinishDisplay.ts` WIP** — depinde de registry comis; neinclus în acest commit.
4. **Scripts `generate/validate-color-registry.mjs`** — utili dar necomiți (pot fi adăugați într-un build import-tooling).
5. **`frontend/package.json`** — scripturi color-registry în diff local, necomise.

---

## 11. Verdict

_Completat la commit — vezi output final agent._
