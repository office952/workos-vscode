# WorkOS UI Polish Strategy

**Date:** 2026-06-11  
**Type:** Architecture / product decision — **no runtime changes**  
**Status:** Active — governs UI work until a dedicated global polish build is chartered

---

## Decision

**Global UI polish is deferred until core flows are stable.**

Do not perform page-local visual polish that modifies the App shell, global CSS, shared components, or cross-page layout without an explicit impact audit.

Page-specific UI work may proceed when it stays scoped to that page’s route and files. Cross-cutting visual changes belong in a separate, reviewed global polish build—not bundled into feature or page builds.

---

## Reason

Recent Figma-driven UI cleanup touched shared areas (`App.tsx` shell, global styles, shared UI primitives, nav/sidebar) and risked unintended impact on other pages.

**Evidence artifact (local archive only — not in repo):**

`C:\Users\offic\workos-local-backups\2026-06-11-employee-payments-rollback\ROLLBACK_SAFETY_GLOBAL_UI_UX_CLEANUP.patch`

- Rollback safety capture for global UI/UX cleanup WIP.
- **Not part of the git tree** — kept on disk for reference only.
- **Do not apply** without a dedicated global UI polish build, explicit scope review, and cross-route impact audit.

Core operator flows (intake → quote → execution, Personal operational pages, registry surfaces) are still evolving. Polishing the shell before those flows stabilize creates churn: the same shared tokens and layout primitives get edited repeatedly, and regressions surface far from the page that motivated the change.

---

## Rules

1. **Page-specific UI changes must stay inside that page** unless explicitly approved.
   - Prefer edits under the page component, page-local helpers, and route-scoped tests.
   - Do not “fix while you’re here” in `App.tsx`, `index.css`, `globals.css`, layout wrappers, or `@/components/ui/*` for a single-page Figma pass.

2. **Shared CSS, shared components, and App shell changes require a dedicated global UI polish build.**
   - Charter: scope list, pages affected, before/after screenshots or Figma frame IDs, and a cross-route smoke checklist.
   - Require impact audit: which routes import the touched module, Vitest/Playwright targets, and operator-critical paths (Work Intake, QuoteWizard, shop floor).

3. **Figma may propose designs, but implementation must be scoped and reviewed.**
   - Figma is input, not an automatic mandate to reshape shared layout.
   - Implementation plan must state: page-only vs global, files touched, and rollback path.
   - Designs that imply shell/nav/token changes are **design-only** until the global polish build is approved.

4. **Final polish pass will cover the full application consistently.**
   - One coordinated pass: typography, spacing, nav, shell, shared components, dark theme tokens, responsive breakpoints.
   - Done after core flows are stable and contract-tested—not incrementally per page.

---

## Allowed now (page-local)

| OK | Examples |
|----|----------|
| Page layout inside route content area | Master-detail on `/employee-payments`, list + detail within page grid |
| Page-scoped demo/state | Local payment recording UI, page filters, tabs |
| Page tests | `EmployeePayments.test.tsx`, route badge tests |
| Page QA / contract docs | Screen contracts under `docs/architecture/PERSONAL_*` |

---

## Not allowed without global polish build

| Blocked / requires charter | Examples |
|----------------------------|----------|
| `App.tsx` shell, sidebar, nav sections | Collapse behavior, nav typography, user menu |
| Global CSS / Tailwind theme | `index.css`, CSS variables, `operator-interactive` utilities |
| `@/components/ui/*` primitives | Button, Badge, Input default styles |
| Cross-page layout wrappers | Shared page headers, content max-width in layout shell |
| “Cleanup” sweeps across `frontend/src/pages/*` | Bulk color/spacing alignment |

---

## Figma workflow

1. **Design** — Figma frames may target a single screen or a full-app vision.
2. **Scope review** — Owner or build lead marks: *page-only* vs *global* before coding.
3. **Implement** — Page-only: implement in page files only. Global: wait for polish build or explicit approval with audit.
4. **Verify** — Targeted tests for the page; cross-route smoke only when shared files changed.

---

## Final polish pass (future)

When chartered:

- Apply tokens, spacing, and component variants once across WorkOS.
- Align Personal, Commercial, Operations, and Settings modules under the same shell rules.
- Run full frontend validate + operator smoke routes after shared changes.
- Document in `docs/qa/BUILD_GLOBAL_UI_POLISH.md` (not yet created).

---

## Related documents

| Document | Relation |
|----------|----------|
| `C:\Users\offic\workos-local-backups\2026-06-11-employee-payments-rollback\ROLLBACK_SAFETY_GLOBAL_UI_UX_CLEANUP.patch` | Local-only rollback capture for risky global UI WIP — **do not apply** without global polish build |
| `docs/qa/BUILD_PERSONAL_EMPLOYEE_PAYMENTS_FIGMA_UI_IMPLEMENTATION.md` | Example of **page-scoped** Figma implementation |
| `docs/architecture/PERSONAL_EMPLOYEE_PAYMENTS_SCREEN_CONTRACT.md` | Page contract without shell changes |
| `docs/audits/WORKOS_FORM_FLOW_AUDIT_AND_FLUID_PROPOSAL.md` | Form/flow architecture (orthogonal to visual polish) |
| `AGENTS.md` | Agent constraints: narrow scope, no drive-by refactors |

---

## Agent / developer checklist

Before editing UI, ask:

- [ ] Is this change confined to one route’s files?
- [ ] Does it touch App shell, global CSS, or shared `ui` components?
- [ ] If yes to shell/CSS/shared: is there an approved global polish build or explicit owner approval + audit?
- [ ] Are tests scoped to the page (or full suite if shared)?
- [ ] Is there a rollback path (revert list or local archive patch — patches are **not** stored in repo)?

If any shared-area edit is required for a page build, **stop** and split: ship page-local scope first; queue shell/CSS for global polish.
