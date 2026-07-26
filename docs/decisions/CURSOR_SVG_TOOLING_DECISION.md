# Decision — Cursor SVG tooling

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Status | Accepted (Better SVG); Visual SVG Editor deferred |
| Owner GO | `INSTALL_VALIDATE_DOCUMENT_CURSOR_SVG_VECTOR_TOOLING` |
| Scope | Developer tooling only |

## Problemă

Lucrul pe SVG-uri reale (litere, logo, candidați chenar/panou) în Cursor necesita preview, zoom și inspecție fără a muta authority-ul geometric din SVG Analyzer WorkOS și fără rescrieri automate.

## Opțiuni evaluate

### A — Better SVG (`midudev.better-svg`)

- Preview în Explorer, zoom/pan, hover, gutter.
- Cod SVG rămâne în editor text (`*.svg` → default editor).
- SVGO integrat ca **comandă manuală** (`betterSvg.optimize`), nu on-save.
- Publisher verificat, Apache-2.0, Open VSX + Marketplace, repo oficial `midudev/better-svg`.
- Versiune validată: `0.5.1` (2026-06-19 pe Open VSX).

### B — Visual SVG Editor (`barbozaa.visual-svg-editor`)

- Editor vizual dedicat („Reopen Editor With… → SVG Editor”).
- Marketplace prezent; Open VSX **absent** (404 la probe).
- Versiune early `0.1.0`, repo cu activitate/stars reduse.
- Risc: rescriere path / normalizare / pierdere precizie la editare vizuală — necesită GO și validare no-mutation separată.
- Nu instalat în acest task.

### C — Alte editoare (ex. `henoc.svgeditor`)

- Nu evaluate pentru instalare; unele colectează transform-uri / rotunjesc zecimale by design — incompatibile cu politica no-mutation fără GO.

## Alegere

**Instalează și recomandă doar Better SVG.**  
Visual SVG Editor → `VISUAL_SVG_EDITOR_EVALUATION_REQUIRED` / Option 3 cu GO owner.

## Motive

1. Acoperă inspectia necesară (preview, zoom, pan, path code, hover).
2. Nu activează auto-SVGO / format-on-save.
3. Supply-chain clară (publisher + Open VSX verified + Apache-2.0).
4. Nu introduce al doilea editor care poate muta geometria.

## Riscuri

| Risc | Mitigare |
|------|----------|
| Optimize manual schimbă precizia (`floatPrecision`) | Interzis pe originale; doar pe copie temporară |
| Activare largă pe TSX/HTML | Acceptabil pentru hover; nu rescrie fără Optimize |
| Confuzie cu Analyzer | Documentat explicit ca developer tooling |

## Owner gate

- Instalare Visual SVG Editor: **necesită GO nou**.
- Orice setare workspace care activează rewrite SVG: **necesită GO**.
- Orice folosire SVGO pe fixtures/client assets: **interzis** fără copie.

## Reevaluation trigger

- Better SVG adaugă auto-optimize on save.
- Publisher / license / marketplace se schimbă neclar.
- Owner cere editare vizuală reală pe contururi (atunci Option 3).
- Conflict Extension Host cu stack-ul Cursor.
