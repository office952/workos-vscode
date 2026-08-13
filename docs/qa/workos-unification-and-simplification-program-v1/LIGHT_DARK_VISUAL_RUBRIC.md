# Light / dark visual rubric

Evidence and severity only. No redesign.

Severity: `OK` · `LOW` · `MED` · `HIGH` · `NOT_APPLICABLE` · `STATE_NOT_REACHED`

Viewport: 1440×900. Themes set via `workos-theme` + `html.light` / `html.dark`.

---

## AppShell

| Axis | light | dark | Evidence |
|------|-------|------|----------|
| text contrast | MED | OK | Light sidebar labels read cool-grey on cool-grey rail (U1 finding still true). Dark nav text is clearer. `001` / `041` / nav-s00 |
| surface hierarchy | MED | OK | Light: sidebar darker than canvas — incomplete day-mode. Dark: shell and canvas align. |
| borders / dividers | LOW | OK | Light section titles (LUCRĂRI) low contrast. |
| hover | LOW | LOW | Collapse and theme toggle have hover; not photographed per-item. |
| focus | STATE_NOT_REACHED | STATE_NOT_REACHED | Keyboard focus ring not systematically tabbed |
| selected / active | OK | OK | Active nav item readable both themes |
| disabled | NOT_APPLICABLE | NOT_APPLICABLE | No disabled nav items |
| status badges | OK | OK | AUDIT / COMPAT / preview chips visible both themes |
| inputs / selects | LOW | OK | Global search: light input sits on light topbar; placeholder dim |
| tables | NOT_APPLICABLE | NOT_APPLICABLE | |
| charts | NOT_APPLICABLE | NOT_APPLICABLE | |
| modals / popovers | OK | OK | User menu raised surface + Deconectare |
| sticky / fixed | OK | OK | Sidebar + topbar fixed; main scrolls |
| scroll areas | OK | OK | `workos-shell-nav` exhausted 0→624; `main` is the page scroller |
| destructive / warning / success | LOW | LOW | Staging chip green; no destructive in chrome except Deconectare hover |

---

## `/dashboard`

| Axis | light | dark | Evidence |
|------|-------|------|----------|
| text contrast | MED | LOW | KPI first-fold: large numbers, **missing human labels** (27 / 0 / 0% / 0 jobs). Dark honesty text on brown panel is readable. `s00-y0` both themes |
| surface hierarchy | HIGH | MED | Stacked banners (next-step + operational truth + gaps) bury the work. Dark is the same stack, better contrast. `s00`–`s02` |
| borders / dividers | OK | OK | Card borders present |
| hover | STATE_NOT_REACHED | STATE_NOT_REACHED | |
| focus | STATE_NOT_REACHED | STATE_NOT_REACHED | |
| selected / active | OK | OK | Breadcrumb “Control producție” selected |
| disabled | NOT_APPLICABLE | NOT_APPLICABLE | |
| status badges | MED | MED | ACTUAL / PROXY / DERIVAT are expert jargon on the primary fold |
| inputs | NOT_APPLICABLE | NOT_APPLICABLE | |
| tables | NOT_APPLICABLE | NOT_APPLICABLE | |
| charts | LOW | LOW | WC util% bars appear only after scroll (`s02-y1299`) — easy to miss |
| modals | NOT_APPLICABLE | NOT_APPLICABLE | |
| sticky / fixed | OK | OK | |
| scroll areas | OK | OK | FULL_VERTICAL_SCROLL PASS 0→1299 |
| destructive / warning / success | MED | MED | Yellow honesty + green OK gaps dominate; no delivery-risk state to judge |

---

## `/quotes`

| Axis | light | dark | Evidence |
|------|-------|------|----------|
| text contrast | OK | OK | IDs, totals, status chips readable. `s00` both themes |
| surface hierarchy | MED | MED | Three money KPIs + technical accordion + 32-card list. Detail empty-state competes with list |
| borders / dividers | OK | OK | |
| hover | LOW | LOW | Card hover exists in CSS; not isolated |
| focus | OK | OK | Search focus captured in first pass |
| selected / active | OK | OK | Selected card ring; filter chip “Toate” |
| disabled | OK | OK | V6 “Trimite în ofertare” disabled on detail — visible disabled treatment |
| status badges | OK | OK | Tarifat purple / Acceptat green both themes |
| inputs / selects | OK | OK | Search + status chips |
| tables | MED | MED | Not a table — card stack. 32 rows require 7 scroll segments |
| charts | NOT_APPLICABLE | NOT_APPLICABLE | |
| modals | STATE_NOT_REACHED | STATE_NOT_REACHED | Send/revision submit out of bounds |
| sticky / fixed | LOW | LOW | List and detail scroll with `main`; detail does not stay pinned while list exhausts |
| scroll areas | OK | OK | PASS on all quote tabs; longest 0→4440 |
| destructive / warning / success | LOW | LOW | Acceptat green; no reject state opened |

---

## `/shop-floor`

| Axis | light | dark | Evidence |
|------|-------|------|----------|
| text contrast | MED | OK | Light: idle machine text dim; workcenter codes (`CNC_ROUTING`) are English/internal |
| surface hierarchy | MED | MED | Next-step banner + Live DB + dense card grid. Print is the only active card |
| borders / dividers | OK | OK | |
| hover | STATE_NOT_REACHED | STATE_NOT_REACHED | |
| focus | STATE_NOT_REACHED | STATE_NOT_REACHED | |
| selected / active | OK | OK | Atelier nav selected; Print machine green |
| disabled | NOT_APPLICABLE | NOT_APPLICABLE | |
| status badges | MED | MED | Idle/active chips OK; `SourceBadge` shared; WC keys are not operator language |
| inputs | NOT_APPLICABLE | NOT_APPLICABLE | |
| tables | LOW | LOW | Queue placeholders inside cards |
| charts | NOT_APPLICABLE | NOT_APPLICABLE | |
| modals | NOT_APPLICABLE | NOT_APPLICABLE | |
| sticky / fixed | OK | OK | |
| scroll areas | OK | OK | PASS 0→818 both roles/themes |
| destructive / warning / success | LOW | LOW | Blocked chip not present (0 blocked) |

---

## Systemic (do not fix in this GO)

1. Light mode sidebar still fails as a day surface (cool rail vs white canvas).
2. Dashboard first fold is audit-banner chrome, not an operator home.
3. Shop-floor and dashboard expose internal codes / provenance jargon as the primary story.
4. Quotes list is a long unvirtualized card stack (7 viewports) — pattern that should be a shared dense list, not page-local cards.
