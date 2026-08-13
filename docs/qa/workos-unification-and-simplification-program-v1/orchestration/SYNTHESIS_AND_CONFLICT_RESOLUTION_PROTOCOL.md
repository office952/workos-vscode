# Synthesis and conflict resolution protocol

## Conflict resolution rule

1. **Evidence beats opinion.** Screenshot + interaction inventory + code/API/doc cite.
2. **System boundary docs beat page-local stories.** Realignment 00–19 and the Systems Alignment Map win over a lane’s “this page feels like the offer hub.”
3. **Primary page card beats observer** for what the page *contains*. Observer beats primary for *pattern* (F) or *edge* (H) or *classify* (G) **only in that dimension**.
4. **If two primaries collide** → `CONTRADICTION_FOUND`, stop the wave, Owner decides. Do not merge quietly.
5. **If UI and API disagree** → log contradiction; do not pick a “user-friendly” lie.
6. **If light and dark disagree** → record both; do not generalize from one theme.
7. **Commercial grain ≠ execution grain** → if a lane treats them as 1:1, reject the global recommendation.
8. **Classify ≠ delete.** `REMOVE_CANDIDATE_ONLY` never becomes a delete task in this program phase.
9. **Local finding ≠ global verdict.** Only ORCH writes backlog rows.
10. **Reviewer veto.** `CONTRADICTION_FOUND` or `INSUFFICIENT_EVIDENCE` blocks any claim that the wave’s synthesis is closed.

## Orchestrator questions (every page, at synthesis time)

Why does it exist · who is it for · what decision does it support · is nav placement honest · does it leak internals · is it duplicated · is there a better home · is UI backed by canonical API · is terminology consistent · are light/dark equivalent · shared primitives vs one-off · overbuilt / under-explained · stay / simplify / merge / move / hide / removal-candidate · downstream dependents · which journey breaks if it changes · necessity vs residue.

Answers go in `canonical/SYNTHESIS.md` with evidence ids. Missing answer = gap, not a guess.

## Duplicate recommendations

Same candidate from two lanes → one backlog row, two evidence links. ORCH is the only writer of `MASTER_SIMPLIFICATION_CANDIDATE_BACKLOG`.

## Premature implementation

Any sentence of the form “change X to Y in code” is **out of bounds** unless Owner later issues an implementation GO. Synthesis may say “candidate: merge these two labels” — not “edit `shellNavigation.ts`.”
