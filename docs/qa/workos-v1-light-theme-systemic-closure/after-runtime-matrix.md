# Light Theme — After-fix runtime matrix

```text
CAPTURED = 2026-08-10
THEME = ThemeProvider / workos-theme + html.light|dark
HEAD_AT_CAPTURE = post mid-flight FE presentation fixes (pre-commit)
RULE = outcome-based P0/P1 only
```

## Proven closures

| ID | Severity | Before | After (runtime) | Verdict |
|----|----------|--------|-----------------|--------|
| RT-P0-01 | P0 | Gross `text-emerald-200` rgb(167,243,208) on white | Gross `text-emerald-700` rgb(4,120,87); net `text-wo-text-primary` rgb(15,23,42); EUR visible | **CLOSED** |
| RT-P0-02 | P0/P1 | Pale slate on LiveCalc metadata / materials | `wo-text-*` + amber/cyan light+`dark:` pairs on LiveCalc + PricingInput + commercial spine | **CLOSED** on operator offer rail |
| RT-P1-01 | P1 | Quotes filter `text-blue-400` | Active chip `bg-blue-50 text-blue-700` / Dark `text-blue-400` | **CLOSED** |
| RT-P1-02 | P1 | Quotes guarded status night chips | Light+`dark:` emerald/amber/blue/rose chip recipes | **CLOSED** |
| RT-CODE-01 | P0 when visible | Quotes `#121B2C` freeze rows | `bg-wo-surface-raised` | **CLOSED** (code path) |
| Sonner authority | P0 authority | `next-themes` orphan import | ThemeContext `resolvedTheme` | **CLOSED** |
| SourceBadge empty/mixed | shared | dark-only tones | light+`dark:` in tokens | **CLOSED** (contract tested) |

## Commercial EUR non-regression

| Surface | Result |
|---------|--------|
| Intake V6 operator offer hero | `653,45 EUR` / net / TVA visible — currency unchanged |
| Quotes detail commercial total | `661,43 EUR` visible on selected Tarifat quote |
| Hardcoded RON invent on Letters Intake | NO |

## Dark regression (ThemeToggle)

| Surface | Result |
|---------|--------|
| Intake V6 offer rail | Gross emerald-200; net primary light; readable |
| Quotes list + active filter chip | Dark shell; chip `dark:text-blue-400` / `bg-blue-600/20` |

## Light route matrix (active V1)

| Route | Light status | Notes |
|-------|--------------|-------|
| `/dashboard` | OK | AppShell coherent |
| `/intake-v6/:id/operator` | OK | RT-P0 closed; screenshot after-light/03 |
| `/quotes` (+ detail) | OK | Filter/chips/EUR; after-light/02* |
| `/orders` | OK / P2 residual | Mono IDs still `text-blue-400` — accent, not unreadability P0 |
| `/execution` | OK | No night hex islands on list |
| `/execution/machine-runs` | OK | |
| `/inventory/pricing` | OK | |
| `/product-system` Letters | OK (baseline) | No new P0 after shared pass |
| `/modules` | OK / P2 | Dense map; no night hex wells |
| `/governance` | OK | |
| `/shop-floor` | OK / P2 | Accent leftovers only |
| `/utilaje` | OK | |
| `/intake` list | OK / P2 | Accent leftovers only |

## Screenshot index

| File | Mode |
|------|------|
| `after-light/03-intake-v6-operator.png` | Light Intake operator |
| `after-light/02-quotes-list.png` | Light Quotes |
| `after-light/02b-quotes-detail.png` | Light Quotes detail |
| `after-dark/03-intake-v6-operator.png` | Dark Intake regression |
| `after-dark/02-quotes-list.png` | Dark Quotes regression |
| `baseline-light/*` | Pre-edit baseline pack |

## Remaining P2/P3 (non-blocking)

- Orders / intake list / shop-floor mono or link accents still on unconditional `text-blue-400`
- Some Intake V6 secondary panels outside LiveCalc/Pricing still carry night-oriented slate/emerald (not on proven P0 commercial hero)
- Volumetric preview / PDF / finish panels outside shared commercial path — polish later
- CSS minify warnings for legacy arbitrary hex selectors (pre-existing build noise)
