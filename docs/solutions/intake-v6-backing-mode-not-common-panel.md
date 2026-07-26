---
title: "backing_mode is individual letter Forex back, not common continuous panel"
date: 2026-07-16
area: intake-v6
tags:
  - volumetric-letters
  - backing_mode
  - conflated-contract
  - gradi-curat
---

# Problem

An Intake V6 attempt treated `backing_mode=none` as “no common continuous Forex/ACM panel behind the letters.” That interpretation stripped (or would strip) individual letter Forex/PVC rear closure, which front-lit volumetric letters need for body closure and LED seating.

# Root cause

**CONFLATED_CONTRACT:** one enum (`none` | `forex_10_no_bevel` | `forex_10_with_bevel`) was overloaded with two product concepts:

1. Individual letter rear closure (material + CNC back ops)
2. Common continuous wall panel / mounting support

Common-panel / template / ACM-bars truth actually lives under `mounting_*` / `mounting_solution`, not under letter `backing_mode`.

# Solution applied (this task)

- Discarded the uncommitted no-backing WIP back to HEAD `6e6ef5d`
- Removed untracked `intakeV6BackingMode.noneContract.test.ts`
- Did **not** keep `installation_template_only` readiness carve-out
- Did **not** invent a new A/B field split

# Binding semantics (until a dedicated architecture GO)

| Concept | Field family |
|---------|--------------|
| Individual letter Forex/PVC back | `finish_setup.backing_mode` (+ per-layer mirrors) |
| Common continuous panel / ACM bars / prep method | `mounting_solution` + template fields |

For front-lit letters: prefer `forex_10_no_bevel` (or with bevel). Do not use `backing_mode=none` to mean “no common panel.”

# Related

- Worklog: `docs/worklog/realignment/2026-07-16_gradi_curat_revert_no_backing_and_restore_owner_truth.md`
- Next gap: `MOUNTING_SOLUTION_MISSING` when only installation template is intended
