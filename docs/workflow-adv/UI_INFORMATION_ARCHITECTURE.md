# Workflow-ADV UI information architecture

## Purpose

Workflow-ADV Platform is a desktop-first operational application. Its UI must guide an operator to valid actions, an administrator to governed configuration, and a developer to diagnostics without confusing these roles or importing the Current WorkOS / Workflow-ADV Lab badge-heavy interface as production UI.

**Lab UI is evidence and diagnostic UI. It is not Platform UI.**

## Primary navigation

```text
Workspace
├─ Operator
│  ├─ My work / queue
│  ├─ Requests
│  ├─ Product review and confirmation
│  ├─ EIC / readiness evidence
│  └─ Exceptions and corrections
├─ Administration
│  ├─ Product templates and composition
│  ├─ Form contracts
│  ├─ Catalogs and operational processes
│  ├─ Versions, promotion, and Freeze
│  └─ Audit
└─ Development
   ├─ Diagnostics
   ├─ Contract and fixture browser
   ├─ Warnings and validation evidence
   └─ Experimental work
```

Navigation exposes only sections available to the current mode and permission. Deep links retain the record/version context and never make an experimental or draft record look operational.

## Page hierarchy

### Operator mode

| Page | Operator outcome | Required content |
|---|---|---|
| Queue | Choose work needing action | prioritization, ownership, status, blockers |
| Request workspace | Capture valid request context | task progress, clear action rail, saved state |
| Product review | Review observed/proposed/manually entered values | source state, confidence when supplied, accept/reject/correct controls |
| Confirmation | Create confirmed Product Truth | explicit confirmation scope, provenance, validation failures |
| EIC/readiness | Understand production-cost evidence and readiness | EIC breakdown/evidence, missing truth, warnings, no frontend recalculation |
| Exception | Resolve a blocked or invalid state | error reason, affected field, valid next action, audit link |

Operator mode is action/form/valid-choice focused. It shows the minimum necessary technical detail and never asks an operator to interpret raw diagnostics to complete routine work.

### Admin mode

| Page | Administrative outcome |
|---|---|
| Template catalog | Manage product/component templates and composition contracts |
| Form System | Govern reusable fields, sections, validation, provenance, and confirmation requirements |
| Catalogs | Manage catalog-backed materials, processes, labor, services, and variants under their owners |
| Version workspace | Start a draft, compare versions, prepare evidence, and request promotion |
| Freeze control | View frozen scope, authorized unfreeze actions, and successor versions |
| Audit | Inspect who changed, promoted, confirmed, froze, or unfroze what and why |

Admin actions are explicit, version-scoped, permission-gated, and audit-producing. Admin mode does not grant a shortcut around operator confirmation or Freeze immutability.

### Dev mode

| Page | Development outcome |
|---|---|
| Diagnostics | Inspect contract validation, API/adapter traces, feature flags, and health |
| Contract/fixture browser | Compare schema versions, fixtures, and expected results |
| Formula evidence | Inspect declared formula ownership, inputs, outputs, and calculation evidence |
| Warnings | Triage non-operator warnings and integration concerns |
| Experimental work | Run isolated draft-only experiments with clear non-operational marking |

Dev mode is for diagnostics, warnings, formula evidence, and experimental work. It is never a hidden production backdoor. It may operate only on a new draft/version, never mutate a frozen operational version in place.

## Record structure

Desktop pages use a stable three-part layout where appropriate:

1. **Context header:** record identity, version, lifecycle status, owner, and essential readiness.
2. **Primary work area:** form, comparison, confirmation, or admin task.
3. **Context/action rail:** blockers, warnings, evidence, provenance, and available valid actions.

On narrow viewports, panels may stack, but the Platform is desktop-first: tables, comparisons, audit detail, complex forms, and multi-step confirmation are designed for keyboard/mouse use before mobile optimization.

## Badge rules

Badges communicate compact state only. They are not the primary explanation, a substitute for a page hierarchy, or the predominant visual language.

| Badge class | Examples | Rule |
|---|---|---|
| Lifecycle | Draft, ready for review, frozen | One primary lifecycle badge per record header |
| Authority | Observed, proposed, confirmed | Display near the affected value; never imply confirmation through color alone |
| Readiness | Blocked, needs input, ready | Pair with actionable text and location of the blocker |
| Risk | Warning, error | Use sparingly; errors always include a recovery path |
| Environment | Lab, Dev, experimental | Persistently distinguish non-operational environments |

Do not use badge stacks to represent every implementation detail. Use progressive disclosure: concise summary first, evidence and diagnostics on demand. A badge must have text, accessible name, and a non-color indicator.

## Status language

Use stable, human-readable language. Do not overload “complete,” “ready,” or “confirmed.”

| Domain | Approved language |
|---|---|
| Analyzer input | Observed; Proposed; Needs confirmation; Rejected |
| Product data | Draft; Confirmed; Corrected; Missing required input |
| Validation | Valid; Warning; Blocked; Error |
| Version governance | DEV_ONLY; READY_FOR_REVIEW; CONTRACT_FROZEN; READY_FOR_IMPLEMENTATION; IMPLEMENTED; RUNTIME_VERIFIED; ACCEPTED |
| Freeze | Freeze off (draft only); Freeze on; Frozen operational version; Unfreeze requested |
| Cost boundary | EIC production cost; CPP reconciliation only |

Avoid “auto-confirmed,” “final” for a draft, “priced” as a proxy for truth, and “ready” without its scope. A page must state whether readiness is for review, implementation, runtime verification, or operational acceptance.

## Core interaction rules

- Present valid choices from the relevant frozen/draft contract; do not expose invalid combinations and silently repair them later.
- Keep required input, provenance, source state, confirmation state, validation errors, and consequences visible at the decision point.
- Require explicit operator confirmation before Product Truth changes. “Save” preserves a draft; it does not imply confirmation.
- Preserve an operator’s corrected value and reason rather than overwriting it with a subsequent Analyzer proposal.
- Frontend displays server/domain calculation evidence; it does not become a second business calculator.
- EIC is the lab reference finish line. Do not turn EIC/CPP display into offer or Execution UI within this scope.

## Accessibility expectations

The Platform meets these baseline expectations:

- full keyboard navigation, visible focus, predictable tab order, and no pointer-only critical action;
- semantic headings, landmarks, form labels, instructions, and programmatic error association;
- errors announced and summarized after validation; focus moves to the summary or first invalid control without losing entered data;
- status changes announced through appropriate live regions without excessive noise;
- color is never the only authority, lifecycle, warning, or validation signal;
- text contrast and focus contrast meet WCAG AA expectations; icons have labels/tooltips where meaning is not obvious;
- tables and comparison views retain headers, responsive alternatives, and screen-reader-readable relationships;
- confirm/destructive/freeze actions explain scope and consequences before commit.

Accessibility is a correctness requirement: an operator unable to perceive a blocker or source state cannot make a reliable confirmation.

## Lab and Platform separation

Workflow-ADV Lab may show many status pills, raw fixture data, diagnostics, and experimental affordances to prove a contract. Workflow-ADV Platform replaces that density with role-specific workflows, clear error recovery, stable page structure, and audit-visible actions.

No Lab screen is promoted merely because it demonstrates data. Promotion transfers the contract, fixtures, tests, and evidence behind the screen; Platform UI is deliberately designed and implemented against those artifacts.
