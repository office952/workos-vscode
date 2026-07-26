---
title: Collaboration Phase 2 help and helper work authority
date: 2026-07-16
problem_type: architecture
component: execution-collaboration
tags: [collaboration, help-request, helper-session, membership, phase-2]
---

# Collaboration Phase 2 — help lifecycle and helper work authority

## Problem

Phase 1 delivered HELPER membership only. Helpers could not discover OPEN help, could not start assist work without being blocked by principal claim guards, and `can_assist` was a lying boolean.

## Solution

- Persist `execution_task_help_requests` (broadcast OPEN multi-accept; targeted accept closes).
- Accept → HELPER membership (`help_accept`); cancel/close does not revoke membership.
- Ajutor pool bypasses `_has_active_session_by_other`; claim pool retains it.
- Helper session start/stop require membership + employee_id; stop ≠ complete; leave ≠ stop.
- Principal authority excludes `role=helper` sessions so assist work never unlocks complete/claim.

## Migration note

Use explicit revision `s58_create_execution_task_help_requests` (from `s57`). Do not `alembic upgrade head` while orphan `s50_*` head remains.

## Related

- Phase 1: `docs/solutions/collaboration-membership-helper-only.md`
- BUILD: `docs/qa/BUILD_PROD_FLEX_COLLAB_PHASE_2.md`
