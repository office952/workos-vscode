# WORKOS F7D — Intake V6 / ACM Commercial Integrity Audit

## Verdict

```text
F7D AUDIT = COMPLETE_WITH_FINDINGS
P0 = 4 (2 commercial finish-insensitivity + 2 ACM inclusion/recap honesty)
P1 = 5 (approx.; see consolidated findings)
P2 = 6+
P3 = 4+
COMMERCIAL INTEGRITY = BLOCKED
INTAKE V6 COMMERCIAL INTEGRITY = BLOCKED
SCHEDULING ROADMAP ADVANCEMENT = HOLD
IMPLEMENTATION = NOT STARTED
PUSH = NOT EXECUTED
MATERIALIZATION GATE = CLOSED
```

## Mini decision carried

F7C accepted PASS_WITH_WARNINGS. F7D authorized as audit-only. Pricing / Product System / Intake redesign / resource-policy / DEC-006 implementation **not** started.

## Identity

| Field | Value |
|-------|-------|
| Checkout | `C:\w\psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| Start HEAD | `43d7a3c5` |
| Remote | `0c8a76cd` · ahead 11 / behind 0 at audit start |
| Stash | `wip-employee-unrelated` intact |
| Working tree | unrelated untracked QA noise left alone |

## Agents

| Agent | Role | Result |
|-------|------|--------|
| A | Intake V6 / ACM UX | Field ledger + ACM matrix + UX; QA workspace exercised |
| B | Commercial E2E | P0 finish→total confirmed live + API |
| C | Resource policy / DEC-006 | Decision packs only; no activation |

## QA workspace

| Field | Value |
|-------|-------|
| workspace_id | `5a5ce742-f50f-47b0-985b-32cc6f2fb6a4` |
| code | `IV6-9C5D9538` |
| route | `/intake-v6-app/.../operator` |
| fixture | `test-bond-litere.svg` |
| writes | Intake draft/config only; **no** `Creează oferta prețuită`; no order/snapshot mutation |

## Coverage

~80% of controls reachable by this fixture (live Steps 1–3 minus offer create). Sibling SVG fixtures inventoried; DXF / multi-segment / logo paths code-documented only.

## Consolidated P0 findings

| ID | Source | Title |
|----|--------|-------|
| AGENT-B-F001 | B | Customer total insensitive to face/cant finish type/color (flat `finisaje_colantare_vopsire` 35 RON/m²) |
| AGENT-B-F002 | B | EIC already knows Oracal 641/651/8500 cost spread >3×; CPP never reflects it |
| A-F1 / B-F005 | A+B | ACM inclusion contradicted: standby vs selected/included vs priced in rail |
| A-F4 | A | Step 3 final recap omits ACM panel already in visible total |

Live proof (Lead-inspected): `agent-b-01-*.png` (Fără finisaj) vs `agent-b-02-*.png` (Oracal 8500 Black) — **Ofertă client = 2.288,75 RON both**. Positive control: mounting paper→Forex **does** move CPP (+10 RON) — framework works; finish rule not authored.

## Root owners (commercial)

1. `backend/data/commercial_rules_volumetric_v2.py` — `finisaje_colantare_vopsire` / `VOL_V2_FINISH_M2_OR_MINIMUM`
2. EIC finish material services vs CPP (no bridge)
3. ACM geometry validator for standalone ACM template (`CRITICAL_GEOMETRY_MISSING`)
4. Intake V6 Step-1 composition / standby messaging

## Resource policy / DEC-006 (Agent C — not implemented)

- Empty ORR allow-list must be **`unknown`**, not silent `workcenter_only`
- Propose formal modes on ORR ops; Owner stamps before activation
- DEC-006: short-term **A** (null+warn); long-term **E** hybrid
- UI copy: “Pregătit” → “Eligibil (cu atenționări)”; no code change in F7D

## Recommended next Owner gate

**Grouped P0/P1 commercial remediation build** (finish branching + ACM inclusion honesty + finish contract vocab).  
**HOLD scheduling** until commercial integrity unblocked.  
Resource enum / DEC-006 remain separate Owner stamps.

## Evidence index

- `agent-a-*.md` / `agent-a-findings-summary.json`
- `agent-b-*.md` / `agent-b-findings.json` / `captures/` / screenshots
- `agent-c-*.md`
- Worklog: `docs/worklog/realignment/2026-08-03_f7d_intake_v6_acm_commercial_integrity_audit.md`
