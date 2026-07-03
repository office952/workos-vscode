# BUILD_INTAKE_V3_SMART_OPERATOR_WORKSPACE_UX

**Date:** 2026-06-20  
**Type:** UX contract + integration plan — **documentation only** (no implementation in this build)  
**Reference mock:** `C:\Users\offic\Desktop\intake-v3-operator-workspace-smart.html`  
**Boundary:** Operator Workspace presentation — no CostEngine, Inventory mutations, ExecutionTask creation, PO, quote pricing logic changes.

---

## 1. Scop

Definim cum arată și se comportă **Intake V3 Operator Workspace** când integrăm:

- structura **Smart Workspace** (Atoms mock HTML),
- motorul **SVG Analyzer** (nest2) — preview + instrumente tehnice,
- backend-ul **WorkOS V3** existent — guards, persistență, 3-step flow.

**Principiu central:** interfață simplă, ușor de parcurs; informația densă stă **ascunsă** și se deschide cu ** săgeată în jos** (expand), nu pe ecran permanent.

---

## 2. Ce păstrăm din mock (format + fonturi)

### 2.1 Layout fix (nu negociabil)

```text
Smart banner        — o linie, acțiune clară
Header              — cod · titlu · litere · fișier
Progress 1–2–3      — LAYERS → REVIEW → CONFIRM
Mini status bar     — layers confirmate · blockers · quote
Conținut pas        — max-width ~920px, centrat
Footer fix          — Back · hint · Next
```

Ordinea pașilor rămâne **`layers → review → confirm`** — identic cu `operatorWorkspaceThreeStepViewModel.ts`.

### 2.2 Fonturi (identice mock-ului)

| Rol | Font | Utilizare |
|-----|------|-----------|
| **UI principal** | **Inter** 400/500/600/700 | body, label, butoane, carduri, formulare |
| **Cod / fișier / ID** | **JetBrains Mono** 500/700 | workspace code, nume SVG, coduri culoare |

Încărcare: Google Fonts — aceeași pereche ca în mock:

```html
Inter:wght@400;500;600;700
JetBrains+Mono:wght@500;700
```

**Reguli tipografice:**

- Body: **14px**, `line-height: 1.6`, `letter-spacing: -0.01em`
- Label formular: **10px**, uppercase, tracking larg, culoare `--tm` (slate muted)
- Input / select: **13px** — un singur rând vizual, fără text explicativ lung dedesubt
- Titlu card: **13px**, bold, uppercase, tracking 0.5px
- Nume layer: **15px** bold
- **Minimum operațional:** 11–12px (deja în `operatorWorkspacePresentation.tsx`); **interzis** text 7–10px în zone operator

### 2.3 Paletă și suprafață (dark cockpit)

Păstrăm tokenii din mock / `ow`:

| Token | Hex | Utilizare |
|-------|-----|-----------|
| `--bg0` | `#0A0F1A` | fundal pagină |
| `--bg1` | `#111827` | carduri, header |
| `--bg2` | `#1E293B` | status bar, secundar |
| `--bg3` | `#0D1321` | input background |
| `--brd` | `#2A3548` | borduri |
| `--em` | `#34D399` | confirmat / OK |
| `--am` | `#FBBF24` | pending / blocker |
| `--bl` | `#60A5FA` | acțiune / activ |

**Light theme:** out of scope — mock-ul are toggle decorativ; WorkOS operator rămâne dark cockpit.

### 2.4 Formulare — simplitate (reguli explicite)

1. **Maxim 2–3 câmpuri pe rând** (`r2`, `r3`); pe mobil → o coloană.
2. **Label scurt**, uppercase mic — fără paragrafe sub câmp.
3. **Select în loc de input** când opțiunile sunt finite (rol layer, finisaj, adâncime).
4. **O singură confirmare vizibilă** per layer (checkbox „Confirm sub-group” / „Confirm setup”) — nu 5 checkbox-uri dispersate.
5. **Reset discret** — link/buton mic „↺ Reset to SVG defaults” în colțul cardului, nu banner.
6. **Note contextuale** — maxim **una** per card (`note-b` / `note-a`); restul în secțiune expandabilă.
7. **Fără tab-uri în tab-uri** — un pas = un scroll vertical liniar.

---

## 3. Progressive disclosure — săgeată în jos

Tot ce ocupă mult vertical **nu** stă deschis by default. Pattern-uri din mock, obligatorii în implementare:

### 3.1 Pattern A — `<details>` / drawer cu ▶ ▼

```text
▶ Auto-derived settings (Geometry, Return/Cant, Lighting)
    ↓ click
▼  [ conținutul rulează în jos ]
```

- Săgeata **▶** când e închis, **▼** când e deschis (ca mock `details>summary::before`).
- Componentă existentă de extins: `OperatorLazyDetails` — păstrează lazy mount (copii doar când e deschis).

**Conținut tipic ascuns:**

- Geometry stats (width, height, depth, perimeter)
- Return / Cant global defaults
- Lighting & PSU (inclusiv manual override)
- Detalii tehnice SVG (sursă, viewBox, policies)
- Panouri nest2: parts, nesting, bond flat, JSON

### 3.2 Pattern B — `derived-wrap` (Review step)

Secțiunea **„Auto-derived settings”** pe pasul Review:

- **Închisă** la intrarea în Review — operatorul vede mai întâi Material breakdown + Readiness.
- Deschidere opțională pentru verificare geometry / lighting.
- Arrow pe rândul toggle, conținut glisează sub header (mock `.derived-wrap`).

### 3.3 Pattern C — layer card expand

- Header layer mereu vizibil: swatch · nume · meta · badge status.
- Body layer **ascuns** până la click pe header (mock `.layer.open .layer-body`).
- Sub-grupuri (RC, PUBLIMEDIA) = mini-carduri în interior — nu layere separate pe pagină.

### 3.4 Pattern D — SVG preview vs dropzone

| Stare | Ce vede operatorul |
|-------|-------------------|
| SVG salvat | **Preview mare** + „Replace SVG” discret |
| Replace / fără SVG | Dropzone (dashed) + „Browse files” |
| Upload în curs | Spinner pe zona preview — **fără** panouri analyzer |

Dropzone **nu** stă permanent sub preview — exact ca mock `showDropzone()` / `simulateUpload()`.

### 3.5 Ce rămâne mereu vizibil (fără săgeată)

- Smart banner (1 mesaj + 1 acțiune)
- Header + progress + mini status bar
- SVG preview (când există fișier)
- Layer strip (chip-uri scurte)
- Layer head (nume + status) — nu body
- Readiness list (linii scurte ✓ / !)
- Footer Back / Next
- Blocker quote (1 frază, nu listă tehnică)

---

## 4. Ce respingem din mock Smart

| Element mock | Motiv |
|--------------|-------|
| Voice commands | zgomot UX, fără backend |
| AI Copilot sidebar | idem |
| Confetti / sound | decorativ |
| Theme toggle light/dark | out of scope |
| Particle background canvas | distragere; fără valoare operațională |
| Estimări € în copilot | pricing = CostEngine, out of scope |

---

## 5. Integrare SVG Analyzer (nest2) — unde intră, fără complicație

| nest2 | Vizibilitate operator |
|-------|---------------------|
| `SvgPreview` | **Mereu** în pasul Layers (când există SVG) |
| Import (Load SVG / browse) | În dropzone ascuns sau overlay Replace |
| `SvgWarningsPanel` | Max 1–2 warnings în banner; rest în drawer |
| `SvgLayerTable`, geometry, parts, nesting, bond DXF, JSON | **Doar** în „Detalii tehnice ▶” |

**Backend WorkOS** rămâne sursa de adevăr (`raw_svg_analysis`, layer roles, guards). nest2 = preview client + debug; nu înlocuiește upload API.

**Import UX combinat:**

- Picker clar (nest2) + drag full-page (WorkOS `IntakeV3OperatorWorkspaceFileDrop`)
- Același endpoint: `uploadIntakeV3WorkspaceSvg`

---

## 6. Mapare mock → componente WorkOS țintă

| Mock CSS / secțiune | Componentă țintă |
|---------------------|------------------|
| `.smart-banner` | `OperatorWorkspaceContextBanner` (extins) |
| `.hdr` | `IntakeV3OperatorWorkspaceHeader` |
| `.progress` | `OperatorWorkspaceProgressBar` |
| `.status-bar` | **nou** `OperatorWorkspaceStatusBar` |
| `.svg-prev` / `.svg-dropzone` | **nou** `OperatorSvgPreviewPanel` + `OperatorSvgImportSurface` |
| `.layer-strip` | layer chips (există) |
| `.layer` / `.subgrp` | `OperatorWorkspaceLayerCard` + setup forms |
| `.derived-wrap` | **nou** `OperatorDerivedSettingsSection` (Review) |
| Material `.mat-grp` | `OperatorWorkspaceMaterialsReadonly` |
| `.rdy` | `OperatorWorkspaceReadinessList` |
| `details` advanced | `OperatorLazyDetails` + nest2 tools |
| `.nav-footer` | **nou** `OperatorWorkspaceFooterNav` |

---

## 7. Faze implementare

| Fază | Scope | Status |
|------|-------|--------|
| **0** | Archive tag `archive/pre-smart-workspace-2026-06-20` | ✅ 2026-06-20 |
| **1** | Preview SVG + import toggle + Inter/Mono + status bar + derived-wrap | ✅ **completed / PASS scoped** — 2026-06-22 |
| **2** | Smart banner actions + footer keyboard nav | backlog |
| **3** | Layer sub-grupuri depth | backlog |
| **4** | nest2 tools în drawer tehnice | backlog |

---

## 8. Criterii PASS (acceptanță UX)

| PASS | FAIL |
|------|------|
| Inter + JetBrains Mono pe operator route | Font system default / monospace amestecat |
| Pas Layers: preview dominant, upload discret | Card mare „SVG upload” permanent |
| Review: auto-derived **închis** la load | Geometry + lighting deschise forțat |
| Orice bloc >6 rânduri are ▶ expand | Tabele/panouri nest2 vizibile fără click |
| Formulare max r2/r3, label scurt | Paragrafe explicative sub fiecare câmp |
| 3-step order neschimbat | Pași noi sau tab-uri paralele dominante |
| Quote guards backend neschimbate | Bypass guards pentru „simplitate” |

---

## 9. Fișiere de referință

| Fișier | Rol |
|--------|-----|
| `intake-v3-operator-workspace-smart.html` (Desktop) | **Source of truth vizual** |
| `tmp/atoms-export/reference/02_DESIRED_UX_DIRECTION.md` | ton cockpit |
| `frontend/.../operatorWorkspacePresentation.tsx` | tokeni `ow` existenți |
| `frontend/.../operatorWorkspaceThreeStepViewModel.ts` | logică pași |
| `docs/qa/BUILD_INTAKE_V3_ATOMS_PARITY_SVG_LAYER_COLOR_UI_E2E.md` | layer swatches / evidence |

---

## 10. Rezumat pentru implementare

```text
Vizual     = mock Smart (format, fonturi, culori)
Formulare  = puține câmpuri, label scurt, confirmare clară
Densitate  = ascunsă în spatele săgeții ▼; preview și status mereu vizibile
Motor      = WorkOS backend + nest2 preview/tools în drawer
Flow       = layers → review → confirm (neschimbat)
```

Următorul build de cod: **Faza 2** — smart banner actions + footer keyboard nav.

---

## 11. BUILD_INTAKE_V3_SMART_OPERATOR_WORKSPACE_ATOMIC_RECOVERY (2026-06-22)

**Branch:** `local/integration-pr4-plus-svg-path` (base `3f4cfbc`)  
**Commit:** `feat(intake-v3): stabilize smart operator SVG workspace`  
**Boundary:** Set 0 shared SVG picker + Set 1 V3 operator workspace only. No Auth, V2, Intake V4, e2e, tmp.

### Delivered

| Area | Change |
|------|--------|
| **Shared picker** | `WorkOsSvgFilePicker` — label+hidden input (nest2 pattern), click + dropzone drag/drop, guard states, input reset for re-upload |
| **Preview** | `sanitizeSvgPreviewSource`, sessionStorage preview per workspace, `OperatorSvgPreviewPanel` |
| **Upload sync** | `uploadSvgFileWithPreview`, inline layer roles, immediate `invalidateSvgDerivedSections` on upload |
| **Backend** | `svg_source_replaced` invalidates layer-role confirmations when same keys / different file |
| **UX** | `OperatorSvgImportSurface`, status bar, font loader, derived-settings wrap, Atoms tokens |
| **Stale fix** | Review geometry clears on upload (loading/null until refresh); header shows current filename/dimensions/parse status |

### sessionStorage boundary

- Key: `intake-v3-operator-svg-preview:{workspaceId}`
- Client-only UX preview; backend upload remains analysis source of truth
- Cleared/rewritten on new upload; optional if storage unavailable

### Tests (PASS scoped)

```text
backend: test_intake_v3_reupload_layer_role_snapshot_invalidation.py — 6 passed
frontend: WorkOsSvgFilePicker, operatorSvgPreview, operatorSvgUploadSync,
          operatorSvgUploadHelpers, IntakeV3SvgUploadPanel, FileDrop,
          operatorWorkspaceThreeStepViewModel — 45 passed
```

### Gaps (Faza 2–4)

- Smart banner keyboard actions
- Layer sub-group depth
- nest2 tools in technical drawer
- V2 `V2SvgStage` migration to shared picker (separate build)
- Auth silent refresh (separate build)
