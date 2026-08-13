# Runtime / browser coordination

## Choice

**Model C — hybrid, with a single runtime owner.**

| Option | Decision |
|--------|----------|
| A. One coordinator captures everything | Rejected as sole model — coordinator would bottleneck and mix capture with synthesis |
| B. Lanes each drive Playwright / MCP | Rejected — role/theme/`workos-dev-role` collisions on one stack; two helpers already proved `window` vs `main` confusion |
| **C. Hybrid** | **Chosen** |

## Why C

- One detached stack (`:3000` + `:8000`). Never kill ports. Never a second `dev.ps1`.
- **RT** (runtime coordinator) is the only agent that: starts/reuses the stack, runs Playwright, changes `workos-theme` / `workos-dev-role`, takes screenshots, writes `orchestration/runtime/`.
- Lanes A–H inspect **code and docs in parallel** at any time.
- A lane that needs a live state files a **capture job** (`runtime/queue/<job>.md`): route, role, theme, tabs, nested scrollers, forbidden mutations.
- RT serializes jobs. One browser context (or one Playwright browser) at a time against the shared stack.
- Isolated Playwright **contexts** (separate `workos-dev-role` / theme via `addInitScript`) are allowed **only** if RT owns them and they do not share a page. Prefer sequential jobs in Wave 2 to prove the model.
- No Owner `dev.db` mutations. Prefer dry-run / existing fixtures / QA-clone.
- Standalone dark shells (`/intake-v6-app`, employee-app) do not use ThemeContext — record `N/A` for theme equivalence, do not “fix” by toggling html class.

## Rules

| Rule | Value |
|------|--------|
| SINGLE_RUNTIME_OWNER | YES |
| PARALLEL_BROWSER_SESSIONS_ALLOWED | **BOUNDED** — only RT-owned sequential jobs in Wave 2; later waves may use parallel Playwright contexts if RT schedules them and they do not share storage |
| Competing Vite/uvicorn | NO |
| Lane sets theme/role ad hoc | NO |
| Worktrees | **Not recommended** for evidence-only — isolated folders are enough. Worktrees add merge noise without isolating the live DB |

## Screenshot contract (RT)

Filename encodes: `role` · `route` · `theme` · `scroll segment` · `tab` · expandable/modal · data state.

Scroll: actual container max (`main.overflow-auto` in AppShell). Nested (`workos-shell-nav`, future list panes) separately. Tab change → restart from `scrollTop = 0`.

## Wave 2

RT captures for lane A (and F/H requests). Lanes B–E do **not** get a browser slot in Wave 2.
