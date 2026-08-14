# Traversal protocol

Binding for every authorized route. Wave 1 applies this to AppShell chrome and the three role homes. Later waves reuse the same protocol.

## 1. Per-route, per-theme

Repeat in **light**, then **dark**:

1. Capture initial viewport at `scrollTop = 0`.
2. **Full scroll exhaustion (mandatory)** — see §1.1. A first viewport or an arbitrary mid/bottom shot is **not** enough.
3. Visit every tab and subtab.
4. Open every accordion / expandable card.
5. Open every drawer / modal / popover that belongs to the **normal** operator journey (do not invent admin-debug paths).
6. Follow every relevant internal navigation. Record destination and relationship. **Do not discover destinations by `a[href]` alone** — see §1.2.
7. Inspect loading, empty, error, disabled, and read-only states when reproducible without mutating Owner `dev.db`.
8. Inspect dense-data and low-data states when an existing fixture can show them.
9. Record screenshots in a deterministic ordered set.

A page is **not** audited until:

- its `PAGE_INTERACTION_INVENTORY` row is reconciled with what was actually opened, and
- every capture appears in `SCREENSHOT_COVERAGE_MANIFEST`.

A folder of PNGs is **not** sufficient evidence.

### 1.1 Full scroll exhaustion (binding)

For every audited page and every tab/subtab state:

1. Start at `SCROLL_START = 0`.
2. Capture the initial viewport.
3. Scroll downward **viewport-by-viewport** on the **actual** scroll container (not `window` if the shell uses an inner scroller).
4. Capture every meaningful newly revealed section.
5. Continue until the container reaches its maximum scroll position (`SCROLL_END = max`).
6. Verify that another scroll attempt reveals no new content (`NEW_CONTENT_AFTER_FINAL_SCROLL = NO`).
7. Record:

```
SCROLL_START = 0
SCROLL_END = max
BOTTOM_REACHED = YES
NEW_CONTENT_AFTER_FINAL_SCROLL = NO
SCROLL_SEGMENTS_CAPTURED = <count>
```

If the page has nested scroll containers, audit **each** relevant scroller separately.

A page/tab is **not** complete if only the first viewport or an arbitrary middle viewport was captured.

WorkOS desktop shell: the primary scroller is `main.overflow-auto` inside `[data-testid=workos-desktop-shell]`. The outer shell is `h-screen overflow-hidden`. Scrolling `window` / `document.scrollingElement` is **invalid** evidence.

Manifest fields required per audited surface:

- `FULL_VERTICAL_SCROLL` = `PASS` / `FAIL` / `N/A`
- `BOTTOM_REACHED` = `YES` / `NO`
- `SCROLL_SEGMENT_COUNT` =
- `NESTED_SCROLL_CONTAINERS` =

### 1.2 Interactive surface discovery (binding)

`INTERACTIVE_SURFACE_DISCOVERY` must include:

- anchors (`<a href>`)
- buttons
- row click handlers
- menu items
- programmatic navigation (`navigate()`, `Link`, `onClick`)
- keyboard-interactive controls

A missing `<a href>` is **not** proof that a row has no navigation.

Wave 5 lesson (keep): initial RT marked `/employees-records/:id` as SNR because it searched only `a[href]`. The list uses row `<button onClick>`. Final truth: `DEFINED_AND_REACHABLE`, `NAVIGATION_GAP = NO`, `/employees-records/7` reached. The initial miss is **SUPERSEDED** / **RESOLVED_BY_GAP_CLOSURE**.

## 2. Coverage values

| Value | Meaning |
|-------|---------|
| `COVERED` | State reached in the live UI and photographed |
| `STATE_NOT_REACHED` | Exists or is suspected; blocked without mutation, missing fixture, or missing role session |
| `NOT_APPLICABLE` | Control does not exist on this surface |

Every `STATE_NOT_REACHED` row must name the blocker.

## 3. Wave 1 navigation edges

Wave 1 does **not** fully audit destination pages.

Wave 1 **must** follow each visible AppShell / role-home nav control **once**, record the actual URL and first viewport, and set `FOLLOWED=YES` in `NAVIGATION_AND_LINK_GRAPH.md`.

Role projection for local proof uses existing `sessionStorage workos-dev-role` (U7). Do not invent a new RBAC path. Do not log out the Owner session permanently.

## 4. Forbidden during traversal

- Creating, editing, sending, accepting, or deleting commercial / HR / inventory records
- Writing Owner `dev.db`
- “Fixing” UI, tokens, or copy while auditing
- Unfreeze, cleanup, redesign, refactor

## 5. Hardcoded-UI observation (not a redesign)

On each audited surface, note whether chrome is page-local or shared (`PageShell`, `SectionCard`, `EmptyState`, `AlertBanner`, `DataTableWrapper`, `StatusBadge`, tokens). Output is a repeat-pattern ledger only.
