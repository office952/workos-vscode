# Workflow-ADV Freeze and version governance

## Rule

**FREEZE ON means immutable accepted operational truth.**

Freeze protects a versioned operational contract and the truth derived under it from silent drift. It is not a UI toggle, a label for a draft, or a substitute for audit.

```text
Frozen v1
  -> create DEV v2
  -> validate
  -> promote
  -> accept
  -> FREEZE ON v2
```

No actor, seed, import, agent, admin workflow, or implementation task may mutate frozen operational version `v1` in place.

## Scope

Freeze applies to the accepted version of the relevant operational truth, for example:

- product/template and composition contracts;
- Form System field/validation/confirmation contracts;
- catalog/resource references used by a version;
- formula ownership and quantity contract;
- Analyzer integration contract reference;
- accepted Product Truth and the provenance that supports it;
- accepted lifecycle/promotion evidence.

The exact aggregate boundary must be explicit in the freeze record. “Freeze everything” is not a valid implementation instruction.

## States

| State | Meaning | Permitted actions |
|---|---|---|
| Draft / DEV | New, non-operational version under development | edit, test, compare, review; clearly label as non-operational |
| Reviewable | Candidate has an assembled promotion package | review, return, approve/reject |
| Contract frozen | Contract semantics are fixed for implementation | implement only against the pinned contract; amend through successor draft |
| Accepted operational | Owner accepts the verified operational version | prepare/perform FREEZE ON |
| FREEZE ON | Immutable accepted operational truth | read, audit, reference, supersede through a successor |
| Unfreeze requested | Exceptional owner decision awaiting action | inspect explicit reason and impact; no mutation yet |

## Version creation

A successor version is mandatory for any semantic change to a frozen version: a form rule, template composition, product truth interpretation, formula input/output, catalog meaning, Analyzer contract mapping, lifecycle state, or operational behavior.

The successor starts as `DEV_ONLY`, identifies its frozen predecessor, and copies only the data necessary for an auditable baseline. It must never reuse the predecessor's version identity.

Minor implementation repairs may be applied without a new semantic version only when they preserve the frozen contract exactly and have evidence proving no truth, input/output, lifecycle, or result changed. If uncertain, treat the change as semantic and create a successor.

## Freeze record

FREEZE ON creates an immutable record containing:

| Field | Requirement |
|---|---|
| Subject and version | Stable identity and version/fingerprint |
| Scope | Explicit aggregate/contract parts covered |
| Lifecycle evidence | Promotion stage, acceptance decision, and required proofs |
| Content identity | Hash/checksum or equivalent immutable revision reference |
| Dependencies | Pinned contract, catalog, template, formula, and Analyzer references |
| Truth provenance | Operator confirmations and source references where relevant |
| Actor and time | Owner identity, timestamp, and authorization basis |
| Reason | Why this version is accepted/frozen |
| Successor policy | How amendments are made through a next version |

Freeze must be queryable and audit-visible. A UI badge without this record is not Freeze.

## Owner-only unfreeze

Unfreeze is an exceptional controlled action available only to the designated owner role. It is not a normal Admin or Dev convenience.

An owner-only unfreeze request must state:

1. the exact frozen subject/version and scope;
2. why a successor version cannot address the issue;
3. operational, pricing, audit, and downstream impact;
4. mitigation/rollback and the authorization decision;
5. every affected snapshot or consumer.

Default disposition is **do not unfreeze**: create `DEV v2`. If the owner authorizes unfreeze, record the decision immutably, preserve the pre-unfreeze artifact, invalidate or explicitly classify affected derived artifacts, and re-run validation/promotion before returning to operational use.

Unfreeze never erases history and never rewrites audit records.

## Interaction with confirmation and snapshots

Product Truth becomes authoritative through operator confirmation. A frozen Product Truth revision remains stable even if:

- a later Analyzer result differs;
- source file processing is repeated;
- a template/catalog draft changes;
- a user opens the old record.

Snapshots and downstream operational handoffs reference the accepted frozen revision and required provenance/hash. They do not re-read mutable Analyzer output or draft configuration to alter a prior accepted result.

## Permissions and responsibilities

| Role | May do | May not do |
|---|---|---|
| Operator | confirm runtime facts within valid choices; view frozen provenance | edit contracts, bypass Freeze, unfreeze |
| Admin | create/manage drafts, prepare reviews, inspect audit | mutate FREEZE ON content, confirm on behalf of operator without explicit authorized workflow |
| Dev | diagnose and implement against draft/frozen contract | use DEV MODE on frozen operational version, alter operational truth |
| Owner | accept versions; authorize exceptional unfreeze | bypass the audit record or mutate history invisibly |
| System/automation | validate and enforce transitions | auto-unfreeze or auto-confirm Product Truth |

## Governance checks

Before FREEZE ON:

- [ ] Version reached `ACCEPTED` through the promotion contract.
- [ ] Scope, identity, dependencies, evidence, and owner decision are complete.
- [ ] Operator confirmation/provenance requirements are satisfied.
- [ ] Required tests and runtime verification are attached.
- [ ] The successor path is clear.

After FREEZE ON:

- [ ] Attempts to alter content are rejected and audited.
- [ ] UI makes frozen status and successor action clear.
- [ ] Consumers resolve the pinned version, not a mutable “latest.”
- [ ] Any change request begins with a new DEV version.

## Prohibited shortcuts

- Editing frozen data via seed, SQL, migration, admin endpoint, or agent automation.
- Re-labeling a changed record as the same frozen version.
- Treating “published” or “active” as equivalent to Freeze without immutability proof.
- Mutating a snapshot because its source template evolved.
- Using unfreeze to avoid normal successor review and promotion.
