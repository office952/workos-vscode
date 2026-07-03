# WorkOS Theme Phase Plan (Day / Night)

**Status:** Plan only — **no ThemeProvider, no toggle, no CSS changes**  
**Purpose:** Safe incremental path to theme support without breaking operational modules  
**Related:** `TypographyGuard.md`, `UI_DO_NOT_BREAK.md`, `SETTINGS_SCOPE.md`, `WORKOS_UI_TOKENS_DRAFT.md`

---

## 1. Current state

| Aspect | State |
| ------ | ----- |
| **Effective theme** | Dark-only in production UI |
| **Surfaces** | Many hardcoded hex (`#0A0F1C`, `#0D1321`, `#111827`, `#1A2236`, `#1E293B`, `#2A3548`, …) in `App.tsx` and pages |
| **Tailwind** | `darkMode: ['class']` in `tailwind.config.ts` |
| **shadcn CSS vars** | `:root` + `.dark` defined in `index.css` — **light vars largely unused** |
| **ThemeProvider** | **Missing** — `next-themes` in package.json but not mounted in `main.tsx` / `App.tsx` |
| **Toggle** | **None** |
| **`color-scheme`** | `html { color-scheme: dark; }` forced in `index.css` |
| **Sonner** | Uses `useTheme()` without provider — fragile alignment |
| **Module tokens** | Intake V6 (`v6.*`), Employee Mobile V2 (`employeeMobileV2DesignTokens.ts`), partial `design-system/tokens.ts` |
| **Draft CSS tokens** | `WORKOS_UI_TOKENS_DRAFT.md` (`--wo-*`) — **not in `index.css`** |

**Verdict from audit:** `THEME_NOT_READY` — implement governance first (this document set = Phase 0).

---

## 2. Why not implement now

1. **Toggle without migration breaks modules** — Intake V6, ProductSystem, Pricing, and shell use incompatible hardcoded dark hex; partial light mode looks broken and hides operational status.
2. **Light mode half-done is worse than none** — Operators lose trust if contrast/readiness badges flip unpredictably.
3. **Typography guards must land first** — Theme migration often shrinks or re-wraps text; 8–9px debt would become unreadable on light surfaces.
4. **Misleading UI must be labeled first (P0)** — Theme polish on wrong KPIs amplifies confusion.
5. **Sonner / shadcn / custom hex three-way split** — Needs provider + shell coordination, not a single PR.

---

## 3. Phases

### Phase 0 — Governance only ✅ (this task)

- Publish `TypographyGuard.md`, `UI_DO_NOT_BREAK.md`, `SETTINGS_SCOPE.md`, `THEME_PHASE_PLAN.md`
- Publish `.cursor/rules/workos-ui-governance.mdc`
- Baseline inventory (read-only grep): count `text-[8px]`, `text-[9px]`, hardcoded hex in `frontend/src`
- **Zero UI changes**

### Phase 1 — ThemeProvider dark-only

**Goal:** Mount provider; default dark; no visual change.

- Add `ThemeProvider` from `next-themes` in `main.tsx` or `App.tsx`
- `defaultTheme="dark"`, `forcedTheme="dark"` or equivalent during transition
- Fix Sonner theme hook alignment
- **No light mode exposure**
- Regression: shell, toasts, auth loading

**Exit criteria:** App looks identical; Sonner stable; no flash of wrong theme.

### Phase 2 — Settings Appearance read-only

**Goal:** IA placeholder per `SETTINGS_SCOPE.md`.

- Add Appearance section/tab **disabled** or read-only
- Copy: “Light mode în pregătire” / link to this plan
- **Does not switch theme**
- Admin-only optional

**Exit criteria:** Users cannot activate light mode from UI.

### Phase 3 — Shell-only theme experiment

**Goal:** Prove class-based dark/light on chrome only.

- Feature flag (env or localStorage `workos-theme-experiment`)
- Migrate **only** sidebar, header, app background in `App.tsx` to shadcn vars or `--wo-*`
- **Operational page bodies remain dark** until Phase 4
- Rollback via flag off

**Exit criteria:** Toggle affects shell only; Intake V6 / ProductSystem / Pricing unchanged visually.

### Phase 4 — Module-by-module token migration

**Order (each with full regression from `UI_DO_NOT_BREAK.md`):**

1. Dashboard + Settings (lower CRITICAL)
2. Quotes / Orders / Execution
3. Inventory + Pricing Registry
4. ProductSystem (HIGH — separate sub-phases: library, editor, dossier)
5. Intake V6 (CRITICAL — keep `v6.*`; map to CSS vars behind flag)
6. Employee Mobile V2 (separate token file — do not force desktop vars)
7. Tablet mode

**Per module:** map hex → `--wo-*` or shadcn semantic tokens; no font size changes bundled.

### Phase 5 — Full light mode

- Enable user-facing light theme only after:
  - Contrast audit on badges, warnings, pricing gates
  - Full regression on all critical routes (desktop + tablet + employee mobile)
  - Settings Appearance functional with default **dark** for existing users
- Pilot with internal admin users first

---

## 4. Fragile files

Do not batch-edit without phase approval:

| File | Risk |
| ---- | ---- |
| `frontend/src/index.css` | Global vars, `color-scheme` |
| `frontend/tailwind.config.ts` | `darkMode`, theme extend |
| `frontend/src/main.tsx` | Provider mount point |
| `frontend/src/App.tsx` | Shell hex, nav, layout |
| `frontend/src/pages/Settings.tsx` | Appearance tab future |
| `frontend/src/components/ui/sonner.tsx` | Theme hook |
| `frontend/src/intake-v6/atoms/intakeV6Presentation.tsx` | V6 typography/surfaces |
| `frontend/src/lib/employeeMobileV2DesignTokens.ts` | Mobile palette |
| `frontend/src/pages/ProductSystem.tsx` + features | Largest hex + micro-type debt |
| `frontend/src/pages/Pricing.tsx` (or inventory/pricing route) | Registry density |
| `frontend/src/components/workos/design-system/tokens.ts` | Shared badge/surface helpers |

---

## 5. Rollback plan

| Mechanism | Action |
| --------- | ------ |
| **Feature flag** | Disable `workos-theme-experiment` → shell reverts |
| **Default dark** | Provider `defaultTheme="dark"`; new users stay dark |
| **localStorage** | Remove keys: `workos-theme`, `workos-theme-experiment` |
| **No DB** | Theme preference must not require migrations for rollback |
| **Provider forced dark** | Emergency: `forcedTheme="dark"` single-line revert |

Document rollback in PR description for any Phase 1+ task.

---

## 6. Baseline metrics (Phase 0 — document only)

Run before Phase 1 (example commands — **do not run as part of theme implementation without recording counts**):

```powershell
# Arbitrary small text (indicative)
rg "text-\[8px\]" frontend/src --count
rg "text-\[9px\]" frontend/src --count

# Hardcoded dark hex (indicative)
rg "#0A0F1C|#111827|#1E293B" frontend/src --count
```

Record counts in the Phase 1 task description to measure migration progress.

---

## 7. Explicit non-goals (all phases until Phase 5 complete)

- No global font-family rebrand
- No redesign of Intake V6 or ProductSystem visual direction
- No removal of mock/live banners for aesthetic unity
- No automatic conversion of all pages in one PR

---

## 8. Checklist for theme-phase tasks

```text
Theme Phase Task:
- Phase number (0–5):
- Files from fragile list touched:
- Visual change expected: yes/no — scope:
- Light mode user-visible: yes/no (should be no before Phase 5)
- Feature flag name:
- Rollback steps documented: yes/no
- Regression pages checked:
- Intake V6 / ProductSystem / Pricing visually unchanged: yes/no
```
