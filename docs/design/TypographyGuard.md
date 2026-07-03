# WorkOS Typography Guard

**Status:** Governance document — **no CSS or component changes**  
**Layer:** Typography rules for all future UI work  
**Related:** `UI_DO_NOT_BREAK.md`, `THEME_PHASE_PLAN.md`, `WORKOS_UI_TOKENS_DRAFT.md`

---

## 1. Purpose

WorkOS is an operational ERP used in office, shop floor, tablet, and employee mobile contexts. Typography is not a cosmetic preference — it directly affects whether operators can read status, pricing, stock, and task information under real conditions.

This guard exists because:

- The codebase contains many arbitrary Tailwind sizes (`text-[8px]`, `text-[9px]`, `text-[10px]`) that are below safe operational readability.
- Critical information (status, readiness, stock, availability, pricing hints) must remain legible on workshop screens and tablets.
- **Intake V6** and **Employee Mobile V2** already define local presentation tokens (`v6.*`, `employeeMobileV2DesignTokens.ts`) that encode deliberate sizing — these must not be overwritten by global polish or theme experiments.
- Random micro-typography during UI cleanup amplifies misleading UI risks (preview totals, badges, KPIs) identified in the full app audit.

This document does **not** fix existing violations. It prevents new ones and guides incremental remediation in approved tasks only.

---

## 2. Minimum typography rules

### Absolute restrictions (new code)

| Rule | Detail |
| ---- | ------ |
| **Forbidden** | `text-[8px]` in any new code |
| **Forbidden** | `text-[9px]` in operational UI (see Exceptions) |
| **Restricted** | `text-[10px]` — only non-critical meta (timestamps, internal IDs, decorative counts) |

### Minimum 11px — operational secondary labels

Use **at least 11px** (`text-[11px]` or `text-xs` where ≥12px) for:

- Status text and status chips
- Readiness indicators
- Operational badges (stock, availability, source, live/mock)
- Stock quantities and unit hints
- Machine/employee availability
- Data source labels (REAL / PREVIEW / MOCK / N/A)
- Secondary operational labels in tables and cards

### Minimum 12px — primary operational content

Use **at least 12px** (`text-[12px]`, `text-xs`, `text-sm`) for:

- Body copy in forms and panels
- Form labels and field values
- Intake V6 operator-facing copy
- Pricing critical info (rates, currency, owner-confirmed gates)
- Task info (title, duration, workcenter)
- Warnings and error messages
- Tablet and mobile operational UI
- Empty-state guidance and next-step copy

### CTA and buttons

- Primary and secondary CTAs must remain readable on tablet/shop floor (typically `text-sm` / 14px via shadcn `Button`).
- Do not shrink button label text below 12px for operational actions (save, validate, price, accept, start task).
- Disabled CTAs must include adjacent copy or tooltip explaining why — not only smaller gray text.

### Standard Tailwind preference

When size maps cleanly, prefer semantic classes:

| Class | Typical use |
| ----- | ----------- |
| `text-xs` | 12px compact operational (verify theme) |
| `text-sm` | 14px body, forms, buttons |
| `text-base` | 16px emphasis, mobile primary |

Use `text-[12px]` / `text-[11px]` only when matching an existing module token scale (Intake V6, Employee Mobile).

---

## 3. Component-specific rules

### Tables

- Header cells: ≥11px, prefer 12px; uppercase labels must not go below 11px.
- Row body: ≥12px for identifiers, amounts, dates, status.
- Numeric columns: right-align; currency/unit visible at ≥11px.
- Action columns: icon buttons need aria-label; text actions ≥12px.
- Do not add denser rows without explicit task scope and regression on Pricing, Quotes, ProductSystem.

### Badges / status chips

- Operational status badges: **minimum 11px** text.
- Use `SourceBadge` or `statusBadgeSizeClasses` from `components/workos/design-system/tokens.ts` where applicable.
- Never rely on color alone — include text (Live, Mock, Preview, Draft, N/A).
- Pricing/readiness gates: ≥12px when they gate an action.

### KPI cards

- Primary value: hierarchy clear; label ≥11px, value ≥14px preferred.
- Subtext explaining REAL vs PREVIEW vs N/A: ≥11px.
- Do not show `0` where `N/A` or `—` is more honest (empty factory, no pricing run).

### Forms

- Labels: ≥12px for editable fields; 11px acceptable only for section overlines in non-operator admin views.
- Helper text: ≥11px; never put critical validation only in ≤10px helper.
- Required/optional must be explicit in label or helper, not only color.
- Units (mm, RON, EUR, kg) adjacent to value, same line or ≥11px sublabel.

### Inputs

- Input text: shadcn default (`text-sm`) — do not override smaller.
- Placeholder-only labels are forbidden for operational fields.

### Warning banners

- Title: ≥12px; body ≥12px.
- Amber/red/blue semantic banners (Inventory mock, Quotes DB-only, Form System read-only) must not be reduced during polish.

### Empty states

- Heading: ≥14px; guidance: ≥12px.
- Distinguish **no data** vs **error** vs **not configured** in copy, not only icon color.

### Tabs

- Tab labels: ≥12px for operator modules; 11px minimum for dense admin diagnostics.
- Active state must not depend on color alone (underline, weight, or background).

### Navigation

- Sidebar items: maintain current readable scale; do not micro-shrink for fit.
- Page titles: ≥18px (`text-lg`+) for primary module headers.

### Mobile / tablet

- Follow Employee Mobile V2 tokens (`min-h-[44px]` touch targets, ≥12px task copy).
- Tablet queue and operator views: no new sub-11px labels.

---

## 4. Allowed patterns

Prefer existing, audited patterns:

| Pattern | Location | Use when |
| ------- | -------- | -------- |
| `v6.*` typography | `intake-v6/atoms/intakeV6Presentation.tsx` | Any Intake V6 UI change |
| Employee Mobile V2 tokens | `lib/employeeMobileV2DesignTokens.ts` | Employee app v2 |
| `SourceBadge` | design-system | Live / Mock / Demo / DB source |
| `statusBadgeSizeClasses` | `components/workos/design-system/tokens.ts` | Status chip sizing |
| shadcn `Button`, `Input`, `Label`, `Badge` | `components/ui/` | New generic UI in admin modules |
| `text-xs`, `text-sm`, `text-base` | Tailwind | Standard body when no module token applies |
| `text-[12px]` | Tailwind arbitrary | Compact operational rows matching module convention |
| `woSurfaces` / token TS | `design-system/tokens.ts` | Surfaces and badge tones |

Do not introduce a parallel typography scale in a single page without owner approval.

---

## 5. Forbidden / avoid patterns

- **No** `text-[8px]` in new code.
- **No** `text-[9px]` in operational UI (production, intake, pricing, inventory, quotes, orders, execution, tablet, employee mobile).
- **No** critical info only in helper text ≤10px.
- **No** operational badges below 11px.
- **No** warning / pricing / task / stock info below 12px.
- **No** color-only status (green dot without label).
- **No** real actions without clear copy (Preview vs Final, Draft vs Sent).
- **No** global font-family change without approved theme phase task.
- **No** drive-by font shrink across files “for consistency” — treat as HIGH fragility (see `UI_DO_NOT_BREAK.md`).

---

## 6. Exceptions

The following may use smaller type **only** when non-operational:

| Context | Max below 11px | Requirement |
| ------- | -------------- | ----------- |
| Governance / architecture docs UI | 10px meta | Must be labeled read-only / reference |
| Module Chain reference events | 10px | Must not imply live production data |
| Debug / diagnostics panels | 9px | Dev-only or admin-only; never on operator path |
| Internal IDs in collapsed meta | 10px | Not used for decisions |

Any exception introduced in a PR must be listed in the task report under **Typography Impact**.

---

## 7. Required UI change report checklist

Every future UI task must include this block in the agent or PR description:

```text
Typography Impact:
- Min font size used:
- Any text-[8px]/text-[9px] introduced: yes/no — where:
- Critical info under 12px: yes/no — where:
- Badges changed: yes/no — components:
- Tables changed: yes/no — pages:
- Forms changed: yes/no — pages:
- Mobile/tablet affected: yes/no — routes:
- Intake V6 affected: yes/no
- ProductSystem affected: yes/no
- Preview vs real labeling touched: yes/no
```

If any answer is `yes` for 8px/9px or critical-under-12px, the task must cite explicit approval or narrow remediation scope.

---

## 8. Relationship to other docs

| Document | Role |
| -------- | ---- |
| `UI_DO_NOT_BREAK.md` | Module fragility and regression pages |
| `SETTINGS_SCOPE.md` | What may appear in Settings (Appearance later) |
| `THEME_PHASE_PLAN.md` | When typography may shift with theme tokens |
| `WORKOS_UI_TOKENS_DRAFT.md` | Future `--wo-*` CSS vars (not yet in `index.css`) |
| `.cursor/rules/workos-ui-governance.mdc` | Auto-applied agent guard for UI tasks |

---

## 9. Remediation note

Existing `text-[8px]` / `text-[9px]` in ProductSystem, Dossier, and legacy pages are **known debt**. Remediation belongs in scoped P2 tasks with regression checks — not in global CSS or drive-by refactors.
