# OWNER_DECISION_STATUS_MATRIX — DEC-001…009

**Fixture:** `92401` / plan `13` · **HEAD:** `8b960a19` · **Authorize:** `BATCH_EXECUTE_MATERIALIZE_AUTHORIZED = False`

Classification legend: `STILL_OPEN` · `IMPLEMENTED_WITH_OWNER_EVIDENCE` · `IMPLEMENTED_WITHOUT_DECISION_RECORD` · `SUPERSEDED` · `PARTIALLY_RESOLVED` · `NOT_APPLICABLE_TO_CURRENT_FIXTURE` · `UNKNOWN_NEEDS_EVIDENCE`

| DEC | Topic (2026-06-30) | Classification | Evidence | Notes |
|-----|--------------------|----------------|----------|-------|
| DEC-001 | `svg_geometry_analysis` non-operational | **IMPLEMENTED_WITH_OWNER_EVIDENCE** *(policy A)* | Not among 18 operational codes; readiness warning still present | Analytics remains outside ops envelope |
| DEC-002 | `premount_bar_preparation` | **NOT_APPLICABLE_TO_CURRENT_FIXTURE** *(default A)* / latent open if premount activated | PD `inactive_modules` includes `structura_suport` pending; premount material roles exist in PD but not PA materials | Do not invent premount ops on 92401 |
| DEC-003 | RETURN lateral canonical | **PARTIALLY_RESOLVED** | Policy A locked in 20A1 F6-D1; envelope still has parent `side_forming`/`return_face_bonding` **and** `RETURN_PROFILE_FACE_BONDING`/`RETURN_PROFILE_MACHINE_FORMING` (F6-D4 sibling dry accept) | Candidates avoided uppercase double-candidate path historically; **runtime ops still carry sibling pairs** — production collapse needs Owner stamp |
| DEC-004 | Painting canonical | **IMPLEMENTED_WITH_OWNER_EVIDENCE** | Exactly one `painting` op; no `PAINTING` | Closed for 92401 envelope |
| DEC-005 | Workcenter source | **PARTIALLY_RESOLVED** | PA ops WC filled ×22; envelope WC null ×18; DEC-005=A dry = do not invent | Upstream WC exists; operational projection gap remains |
| DEC-006 | estimated_minutes | **PARTIALLY_RESOLVED** *(accepted risk A)* | Null ×18 envelope + PA; warn `PLANNING_MINUTES_SOURCE_REQUIRED` | Honest null; not production-scheduling ready |
| DEC-007 | Dependency model | **PARTIALLY_RESOLVED** | `depends_on_task_ids` present; topo display implemented (`89e021c7`); chain-like, not proven finish-aware DAG | Dry/MVP deps OK; production DAG still open |
| DEC-008 | Step 9B UI read-only | **IMPLEMENTED_WITH_OWNER_EVIDENCE** *(supersedes old “NOT_STARTED” app-flow note)* | Ops-graph RO + DEC strip + gap tags + frozen materials (`8b960a19`) | App-flow doc still lags |
| DEC-009 | POST materialize | **STILL_OPEN** as live **A / BLOCKED** | Gate module; authorize false; further POST blocked; MAT-02 historical scoped write already produced 18 ops | **Remain blocked** for additional materialize/execute |

---

## Explicit answers

| Question | Answer |
|----------|--------|
| RETURN lateral still produce duplicate tasks? | **Yes, semantic sibling pairs remain in the 18 ops** (parent forming/bonding + `RETURN_PROFILE_*`). Not identical code duplicates; production ownership collapse still open (F6-D4). |
| `painting` single canonical owner? | **Yes** — one `painting` op. |
| Workcenter authoritative for 18 ops? | **No on envelope.** Authoritative WC strings exist on PA operations, not copied onto operational tasks. |
| Planning minutes real source or fallback? | **Neither filled** — null + warning; accepted risk, not invented fallback. |
| DAG semantic or technical order? | **Technical dependency edges present**; display topo is semantic-over-deps for readability. Not proven finish-aware shop DAG. |
| Topo represents deps without rewriting SEQ? | **Yes** — dependency display order + original SEQ with gaps. |
| Step 9B read-only realized? | **Yes** on ops-graph (+ materials RO). Old architecture flow saying NOT_STARTED is drift. |
| DEC-009 still remain blocked? | **Yes** — live A; authorize false; further POST blocked. |
| Any evidence allowing (further) materialization? | **No.** Envelope already materialized; additional materialize/execute lacks Owner GO and preconditions (qty ownership, WC projection, production RETURN collapse, minutes policy for prod). Default recommendation: **do not materialize again**. |

---

## Closed vs open summary

**Really closed / accepted for current stage**

- DEC-001 policy A (for this fixture)
- DEC-004 painting canonical
- DEC-008 Step 9B-style RO surface (ops-graph)
- DEC-006 null honesty for dry/stage
- Topo+SEQ display
- Frozen materials RO honesty
- DEC-009 further-write blocked

**Really open**

- DEC-003 production sibling collapse
- DEC-005 envelope WC projection
- DEC-006 production minutes source
- DEC-007 production DAG
- DEC-009 any new execute/materialize GO
- Material quantity & active-variant ownership (not numbered DEC-00x but blocking planning)
- Material → operation contract
