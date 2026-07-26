---
title: Phase 2 collaboration integrity — requester cancel and complete→help close
date: 2026-07-16
problem_type: correctness
component: execution-collaboration
tags: [help-request, cancel-authority, completion, multiprocess, sqlite]
---

# Phase 2 collaboration integrity — requester cancel and complete→help close

## Problem

Phase 2 shipped help lifecycle and helper sessions, but closure found blocking integrity gaps: any route-eligible employee could cancel OPEN help; operator/mobile complete could leave OPEN help after idempotent retries; helper session start and help close lacked durable cross-process guarantees; ORM `create_all` omitted the s58 OPEN partial unique index.

## Solution

- Enforce **requester-only cancel** in `_close_like` before terminal short-circuit; targeted helpers use **decline**.
- Call **`close_open_help_for_task`** on every successful Operator/Mobile complete path, including verified `already_completed` retries.
- Treat operator `task_not_started` as idempotent complete **only** when reality shows prior explicit completion (`completed_by_*` / `status=completed`); tighten `end_task` so helper STOP does not count.
- Serialize helper start via reality `for_update`; closer uses task lock + `FOR UPDATE` on OPEN rows; declare ORM partial unique mirroring s58.
- Prove with focused pytest + real HTTP `POST /api/v1/operator/task-action` complete on order 23099.

## Limitations

SQLite does not honor `FOR UPDATE`; process-local asyncio locks are supplementary. Completion and help close remain separate commits because RealityService commits internally — the closer is retry-safe.

## References

- Worklog: `docs/worklog/realignment/2026-07-16_prod_flex_collaboration_phase_2_integrity_correction.md`
- Plan: `.compound-engineering/prod-flex-collaboration-phase-2-correction/plan.md`
- Runtime evidence: `docs/qa/_phase2_correction_runtime_evidence.json`
