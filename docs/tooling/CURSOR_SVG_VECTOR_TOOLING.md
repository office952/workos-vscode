# Cursor SVG vector tooling (developer)

| Field | Value |
|-------|-------|
| Status | Approved for Cursor developer use |
| Extension | Better SVG |
| Extension ID | `midudev.better-svg` |
| Version validated | `0.5.1` |
| License | Apache-2.0 |
| Role | Developer preview / inspect only |
| Runtime authority | **None** — not part of WorkOS product runtime |

## Scop

Îmbunătățește lucrul tehnic cu fișiere SVG în Cursor:

- inspecție vizuală, preview, zoom / pan;
- observarea path-urilor, viewBox, fill/stroke, transform;
- debugging vizual al inputului față de așteptări;
- SVGO **manual** (numai pe acțiune explicită).

**Nu** este authority pentru geometria produsului.  
**Nu** înlocuiește SVG Analyzer WorkOS.  
**Nu** decide roluri (literă / logo / chenar / panou Alucobond), materiale, procese, taskuri sau preț.

## Flux canonic (neschimbat)

```text
SVG încărcat
→ SVG Analyzer detectează și măsoară
→ operatorul selectează și confirmă rolul
→ ProductDefinition salvează configurația
→ Product System compilează
→ ProductAggregate proiectează
→ CPP calculează comercial
→ task_rules existente → tasking existent
```

## Extensia aprobată

| Item | Value |
|------|-------|
| Name | Better SVG |
| Publisher | midudev (Miguel Ángel Durán) |
| Marketplace | https://marketplace.visualstudio.com/items?itemName=midudev.better-svg |
| Open VSX | https://open-vsx.org/extension/midudev/better-svg |
| Repository | https://github.com/midudev/better-svg |
| Engines | VS Code / Cursor compatible `^1.85.0` |

### Instalare

**CLI (verificat pe această mașină):**

```powershell
cursor --install-extension midudev.better-svg
```

**UI:** Extensions → caută exact `midudev.better-svg` → publisher `midudev` → Install.  
Repornește Extension Host dacă preview-ul nu apare.

### Dezinstalare / rollback

```powershell
cursor --uninstall-extension midudev.better-svg
```

Sau Extensions → Better SVG → Uninstall.

Repo rollback:

1. Elimină `"midudev.better-svg"` din `.vscode/extensions.json` (păstrează alte recomandări).
2. Dacă se revine la ignorarea completă a `.vscode/`, restaură linia `.vscode/` în `.gitignore` numai cu GO (carve-out-ul actual permite doar `extensions.json`).
3. Nu șterge documentația istorică fără GO.
4. Nu atinge SVG-uri client / fixtures.

## Setări (chei reale)

Sursă: `package.json` contribuții Better SVG `0.5.1`.

| Key | Default | Policy WorkOS |
|-----|---------|----------------|
| `betterSvg.autoReveal` | `true` | OK — doar UI preview |
| `betterSvg.autoCollapse` | `true` | OK |
| `betterSvg.enableHover` | `true` | OK pentru inspect |
| `betterSvg.showGutterPreview` | `true` | OK |
| `betterSvg.defaultColor` | `#ffffff` | preview only |
| `betterSvg.removeClasses` | `true` | **doar la Optimize manual** |
| `betterSvg.removeComments` | `true` | **doar la Optimize manual** |
| `betterSvg.removeDoctype` | `true` | **doar la Optimize manual** |
| `betterSvg.cleanupIds` | `false` | lăsat default; nu activa fără GO |
| `betterSvg.floatPrecision` | `3` | **doar la Optimize manual** — poate schimba precizia |
| `betterSvg.multipass` | `true` | **doar la Optimize manual** |

Extensia setează `workbench.editorAssociations["*.svg"] = "default"` ca să rămână editorul text (cod accesibil).

### Reguli no-mutation

- **Nu** rula `Better SVG: Optimize SVG` pe SVG-uri originale / client / fixtures fără copie temporară.
- **Nu** există auto-SVGO on save în această versiune — păstrează așa.
- **Nu** activa format-on-save specific SVG fără GO owner.
- Nu rotunji / flatten / rescrie path-uri fără acțiune explicită pe o **copie**.

## Extensia secundară (neinstalată)

`barbozaa.visual-svg-editor` (Visual SVG Editor) — **evaluare separată**, nu instalată în acest task.

Motive: maturitate early (`0.1.0`), editor vizual care poate rescrie fișierul, dublare parțială cu Better SVG, necesită GO suplimentar.  
Vezi `docs/decisions/CURSOR_SVG_TOOLING_DECISION.md`.

## Validare (rezumat)

Vezi `docs/audits/2026-07-17_cursor_svg_vector_tooling_validation.md`.

Fișiere de test (nemodificate):

| ID | Path | Rol |
|----|------|-----|
| A | `fisiere-teste-svg/litere-vol-1-layer.svg` | litere / path-uri multiple |
| B | `fisiere-teste-svg/logo.svg` | simbol / grup |
| C | `fisiere-teste-svg/gradi-curat.svg` | litere + contururi / candidat chenar |

## Boundary — SVG Analyzer WorkOS

| Tooling (Better SVG) | SVG Analyzer (runtime) |
|----------------------|------------------------|
| Preview, zoom, hover | Parsing, normalizare, ID-uri |
| Inspecție vizuală | Măsurători, perimeter, area, bbox |
| Debug developer | Detectare contururi / propunere rol |
| SVGO manual opțional | Persistă doar ce confirmă operatorul → ProductDefinition |

Operatorul confirmă: fundal, Alucobond casetat, intoarceri, L1/L2, adâncime, colț service, cadru interior.

## Direcție Alucobond casetat (design intent — fără implementare)

```text
SVG Analyzer identifică un contur închis
→ candidat fundal / panou
→ operator selectează
→ confirmă ALUCOBOND_CASED_PANEL
→ setează profilul casetării
→ ProductDefinition salvează
→ Product System compilează
```

Setări viitoare (intent only): `svg_support_element_id`, width/height/area/perimeter, `fold_count`, `l1_mm`, `l2_mm`, `finished_depth_mm`, back return, grosime Alucobond, `service_corner`, cadru interior, profile type, mounting-hole spacing, decupaje tehnice, hidden wiring, PSU position.

### Terminologie

| Owner-facing (RO) | Cod tehnic |
|-------------------|------------|
| Contur / Chenar / Fundal | — |
| Panou Alucobond casetat | `ALUCOBOND_CASED_PANEL` |
| Adâncime casetă | `finished_depth_mm` |
| Prima / a doua întoarcere | `l1_mm` / `l2_mm` |
| Colț de service | `service_corner` |
| Cadru interior / Decupaje tehnice | — |
| Element SVG selectat | `svg_support_element_id` |
| Număr întoarceri | `fold_count` |

## Security notes

- Publisher verificat pe Open VSX (`verified: true`).
- Dependință runtime declarată: `svgo@4.0.1` (bundled în extension pack).
- Optimize folosește `WorkspaceEdit` **numai** pe comanda explicită Optimize — nu pe open/preview/zoom.
- Nu descărca `.vsix` de pe site-uri terțe neoficiale.

## Troubleshooting

| Simptom | Acțiune |
|---------|---------|
| Preview lipsă | Confirmă `midudev.better-svg` instalat; deschide `.svg`; Developer: Reload Window |
| SVG se deschide ca binary | Verifică `workbench.editorAssociations` pentru `*.svg` = default |
| Fișier schimbat după Optimize | Nu folosi Optimize pe originale; restore din git / backup |
| Conflict cu alt SVG editor | Dezinstalează editorul vizual agresiv; păstrează Better SVG |

## Modules / Governance (viitor — fără sync acum)

- **Modules:** notează ulterior că tooling-ul Cursor este developer-only; runtime remains SVG Analyzer → PD → Product System → CPP → tasking.
- **Governance:** regula mare rămâne — Analyzer propune, operator confirmă, PD păstrează, Product System compilează, CPP calculează, tasking execută. Extensia Cursor **nu** intră în governance runtime.

## Linkuri

- Decision: `docs/decisions/CURSOR_SVG_TOOLING_DECISION.md`
- Validation: `docs/audits/2026-07-17_cursor_svg_vector_tooling_validation.md`
- Worklog: `docs/worklog/realignment/2026-07-17_cursor_svg_vector_tooling_installation.md`
