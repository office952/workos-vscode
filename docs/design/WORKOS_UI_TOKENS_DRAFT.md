# WorkOS UI Tokens Draft (`--wo-*`)

**Status:** Document-only — **fără implementare CSS**  
**Data:** 2026-06-12  
**Layer:** WorkOS semantic tokens — complementar shadcn, nu înlocuitor imediat

---

## 1. Scop

Propune un set unic de **custom properties CSS** prefixate `--wo-*` care:

- formalizează hex-urile deja folosite operațional în pagini
- reduc duplicarea `bg-[#111827]` / `border-[#1E293B]`
- rămân **documentate** până la Phase 2 (primitivi) / Phase 4 (`index.css`)

> **Notă explicită:** Niciun token din acest document nu este încă definit în `index.css` sau aplicat în componente.

---

## 2. Surfaces

| Token | Valoare | Rol |
|-------|---------|-----|
| `--wo-bg-app` | `#0A0F1C` | Fundal pagină full-bleed (ex. TabletMode) |
| `--wo-bg-shell` | `#0D1321` | Zonă shell / panouri secundare închise |
| `--wo-bg-surface` | `#111827` | Card principal, listă, panou conținut |
| `--wo-bg-surface-raised` | `#1A2236` | Card KPI, rând selectat, panou detaliu |
| `--wo-bg-input` | `#0B1220` | Câmpuri formular pe fundal dark |
| `--wo-bg-inset` | `#0B0E13` | Zone reci / inset / well |

### Usage rules — surfaces

**Do:**

- Folosește `--wo-bg-surface` pentru carduri standard de listă
- Folosește `--wo-bg-surface-raised` pentru KPI tiles și panouri de detaliu sticky
- Păstrează un singur nivel de „ridicare” per zonă (surface → raised, nu raised → raised)

**Don't:**

- Nu adăuga un al 4-lea nivel de fundal fără decizie owner
- Nu amesteca `--wo-bg-app` cu shadcn `--background` în același viewport fără migrare planificată
- Nu folosi white / light gray pentru carduri în module operaționale dark

---

## 3. Borders

| Token | Valoare | Rol |
|-------|---------|-----|
| `--wo-border-subtle` | `#1E293B` | Contur card standard, separator discret |
| `--wo-border-strong` | `#2A3548` | Contur raised cards, input focus adjacency |

### Usage rules — borders

**Do:**

- `--wo-border-subtle` pe carduri listă și secțiuni inactive
- `--wo-border-strong` pe KPI cards și nested panels

**Don't:**

- Nu folosi `border-slate-600` ad-hoc când tokenul semantic există
- Nu folosi borduri colorate ca substitut pentru status badge (status = semantic token separat)

---

## 4. Text

| Token | Valoare | Rol |
|-------|---------|-----|
| `--wo-text-primary` | `#F2F5F7` | Titluri, valori principale |
| `--wo-text-secondary` | `#94A3B8` | Body secundar, descrieri (notă: cod folosește uneori `#94A3BD` — aliniere la migrare) |
| `--wo-text-dim` | `#5C6B80` | Meta, timestamps, placeholder discret |
| `--wo-text-nav-active` | `#3B82F6` | Item nav activ, link curent |

### Usage rules — text

**Do:**

- Primary pentru conținut care necesită acțiune
- Secondary pentru etichete de câmp și subtitluri
- Dim pentru `text-[10px]` meta / uppercase labels

**Don't:**

- Nu folosi `--wo-text-primary` pe paragrafe lungi de ajutor (secondary)
- Nu reduce contrast sub `#5C6B80` pe fundal `#111827` (WCAG operațional minim)

---

## 5. Semantic colors

| Token | Valoare | Rol |
|-------|---------|-----|
| `--wo-accent-primary` | `#3B82F6` | CTA principal, link activ, accent nav |
| `--wo-status-success` | `#33D499` | Succes, done, live DB |
| `--wo-status-warning` | `#FABF24` | Atenție, mock data, pending review |
| `--wo-status-partial` | `#FA913D` | Parțial plătit, progres incomplet |
| `--wo-status-danger` | *TBD — red family* | Eroare, blocked, respins — **valoare exactă de decis owner** |
| `--wo-status-info` | `#60A5FA` | Informativ, viewed, info panel |
| `--wo-accent-violet` | `#8B5CF6` | Locked / snapshot / special state |
| `--wo-accent-cyan` | `#22D3EE` | Opțional — accent secundar (ex. viewed quote) |

### `--wo-status-danger` — TBD

Candidați din cod existent:

- Tailwind destructive dark: `hsl(0 62.8% 30.6%)` (~`#7F1D1D` bg family)
- Badge respins: `text-red-300` / `bg-red-900/40` / `border-red-700`
- **Decizie owner:** alege o singură valoare hex + pereche bg/border pentru badge danger

### Usage rules — semantic

**Do:**

- Un singur accent primary per viewport
- Success / warning / danger doar pentru **semnificație**, nu decor
- Partial distinct de warning (plăți parțiale ≠ mock data)

**Don't:**

- Nu folosi `--wo-accent-primary` pentru status success (confuzie CTA vs stare)
- Nu colora text body integral în roșu — folosește badge sau border-left panel

---

## 6. Typography

| Rol | Mărime | Note |
|-----|--------|------|
| Page title | `20px` | `font-semibold`, `--wo-text-primary` |
| Page subtitle | `13px` | `--wo-text-secondary` |
| Section title | `14px` | echivalent `SectionHeader` curent |
| Label / meta | `10px` uppercase | tracking ușor, `--wo-text-dim` |
| Body | `13px` | densitate operator; echivalent `text-[13px]` |
| KPI value | `22px` | `font-bold`, mono opțional pentru unități |
| Codes / IDs | mono | `font-mono` — ORD-*, QT-*, cod operație |

### Font stack (implicit curent)

- UI: system / Inter / sans din tema existentă
- Mono: pentru coduri business și valori tehnice

---

## 7. Radius

| Token | Valoare | Utilizare |
|-------|---------|-----------|
| `--wo-radius-sm` | `6px` | Badge, chip, input compact |
| `--wo-radius-md` | `8px` | Card standard (`rounded-lg` echivalent) |
| `--wo-radius-lg` | `12px` | Feature cards mari, preview areas, tablet tiles |

### Usage rules — radius

**Do:**

- Badge status: `--wo-radius-sm` (recomandare owner Phase 0)
- Card listă: `--wo-radius-md`
- Tablet station picker: `--wo-radius-lg` permis

**Don't:**

- Nu folosi `rounded-2xl` global fără context tablet/touch
- Nu amesteca badge pill (`rounded-full`) cu charter rectangular fără decizie

---

## 8. Spacing

| Context | Valoare | Note |
|---------|---------|------|
| Page content padding | `16px` | compatibil cu layout curent |
| Page header padding | `24px` | polish viitor — optional incremental |
| Card interior | `p-4` (16px) | default card |
| Dense operator gaps | `8–12px` | OperatorView, tablet, rânduri listă compactă |

### Usage rules — spacing

**Do:**

- Păstrează `gap-2` / `gap-3` în zone dense
- Header module: `mb-4` / `mb-6` consistent per modul după Phase 3

**Don't:**

- Nu crește padding global shell în Phase 3 (doar Phase 4)
- Nu comprima sub `8px` între badge și label acționabil (touch target)

---

## 9. Do / Don't — exemple concrete

### Surfaces

```text
DO:   card listă → bg --wo-bg-surface + border --wo-border-subtle
DO:   KPI tile  → bg --wo-bg-surface-raised + border --wo-border-strong + border-top accent
DON'T: KPI tile → bg --wo-bg-surface fără diferențiere față de listă
DON'T: trei nuanțe ad-hoc (#1A1A1A, #0D1E0D) fără mapare token
```

### Status vs accent

```text
DO:   buton "Trimite ofertă" → --wo-accent-primary
DO:   badge "Acceptat" → --wo-status-success (background semantic diluat)
DON'T: badge verde cu același hex ca butonul primary alături
```

### Data source

```text
DO:   Live DB → success family (--wo-status-success)
DO:   Mock    → warning family (--wo-status-warning)
DON'T: ascunde badge-ul când source === mock
```

---

## 10. Migration notes — hex existente → `--wo-*`

Mapare din codul curent (pagini comerciale / operator):

| Hex / clasă inline frecventă | Token țintă |
|------------------------------|-------------|
| `#0A0F1C` | `--wo-bg-app` |
| `#0D1321` | `--wo-bg-shell` |
| `#111827` | `--wo-bg-surface` |
| `#1A2236` | `--wo-bg-surface-raised` |
| `#1E293B` | `--wo-border-subtle` |
| `#2A3548` | `--wo-border-strong` |
| `#0B1220` | `--wo-bg-input` |
| `text-slate-200` | ~ `--wo-text-primary` |
| `text-slate-400` / `500` | ~ `--wo-text-secondary` / `--wo-text-dim` |
| `border-blue-500/50` (selected) | `--wo-accent-primary` + opacity |
| `bg-emerald-900/30` (Live DB) | `--wo-status-success` + alpha pattern |
| `bg-amber-900/30` (Mock) | `--wo-status-warning` + alpha pattern |

### Relația cu shadcn (`index.css`)

| shadcn (`.dark`) | Strategie |
|------------------|-----------|
| `--background`, `--card`, `--muted` | Rămân active pentru componente ui/ (Dialog, Badge shadcn) |
| `--wo-*` | Layer WorkOS pentru pagini operaționale |
| Phase 4 | Mapare optională `--card` → `--wo-bg-surface` după validare |

Migrarea se face **pagină cu pagină** în Phase 3, nu prin rescriere `index.css` upfront.

---

## 11. Implementare viitoare (checklist)

Când Phase 2/4 autorizează cod:

1. Adaugă bloc `:root` / `.dark` cu `--wo-*` în `index.css` (sau fișier dedicat importat)
2. Extinde `tailwind.config` cu `wo.*` colors referind `var(--wo-*)`
3. Înlocuiește hex inline în modulul țintă
4. Rulează Vitest targeted + smoke vizual manual
5. **Nu** declara `validate:frontend` green fără audit TS separat

---

*Document draft — valorile pot fi ajustate de owner în Phase 0 înainte de implementare.*
