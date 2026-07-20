# Artwork Understanding — Operator Teaching Model

| Field | Value |
|-------|--------|
| Status | **Architecture direction (docs)** — not implemented as a live assistant |
| Date | 2026-07-20 |
| Scope | Volumetric letters artwork interpretation & Product Truth |
| Related | Build 2 GO suspended — see plan addendum |
| Ownership boundary | **[`2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md`](./2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md)** — desktop app owns file analysis; WorkOS consumes/reviews/confirms only |

---

## 1. Verdict

Volumetric letters need a clear split between **observation** (deterministic, from the external desktop analysis app), **interpretation** (assisted, future AI — not WorkOS Product Truth authority), and **confirmation** (operator). Product Truth stores only confirmed truth. Grouping is not “one SVG layer = one commercial group” by default — the operator declares `by_layer` or `by_color`. When the system is unsure, it must stop and ask, not invent groups.

**Permanent limit (2026-07-20):** WorkOS must not implement or extend SVG/DWG/DXF (or other graphic) parsers, geometry extractors, auto-grouping, or file-to-Product-Truth conversion. See External Artwork Analysis Ownership.

```text
Codul observa.
AI-ul interpretează.
Operatorul confirmă.
Product Truth păstrează.
Quantity Builder deduce.
CostEngine calculează.
Producția execută.
```

Clarification: code is not logic-free. Code must be free of **assumptions about human intent**.

---

## 2. Reason for realignment

Owner discussion showed the Build 2 operator-closure plan rested on an incomplete premise: treating detected layers / fixture-like names as stable commercial groups. That confuses parser observations with Product Truth and blocks honest uncertainty.

---

## 3. Previous model problem

- Constructive group assumed equal to one layer / one `group_key`.
- Detected labels (Maria, Ioana, Soare, Georgeta, etc.) treated as if they were domain concepts.
- Parser output mapped too directly toward persistent instances and UI chips.
- Silent continuation and technical badges risked masking misunderstanding.
- Orphan / split-merge UX and LED ownership were planned before grouping truth was closed.

---

## 4. Artwork observation vs interpretation

| Layer | Owns | Must not |
|-------|------|----------|
| **Observation (code)** | Paths, layers, fills, metrics, hashes | Guess intent, invent groups, write Product Truth |
| **Interpretation (assistant, future)** | Explanations, proposals, questions, precedent lookup | Decide, silent fill, write commercial/execution systems |
| **Confirmation (operator)** | Grouping mode, group membership, commercial properties | Be replaced by confidence scores |
| **Product Truth** | Confirmed facts only | Hold unconfirmed proposals |

---

## 5. Layer definition

**Grouping by layer:** one layer holds letters/objects that share the same constructive and commercial properties end-to-end (face, return, back, finish, depth, lighting, mounting, and other shared construction properties).

The layer **name** is an observed label, not permanent identity.

---

## 6. Color grouping definition

**Grouping by color:** objects sharing the same fill/stroke color may form one constructive group with shared commercial properties.

The grouping color is **not** automatically the final production color.

---

## 7. Grouping mode contract

Operator declares or confirms exactly one initial mode:

```text
grouping_mode = by_layer
grouping_mode = by_color
```

Rules:

- Do not auto-combine methods.
- Do not guess from text, names, position, shape, proximity, layer+color together, fixture names, or fuzzy matching.

---

## 8. Operator responsibility

- Prepare artwork in a canonical mode (layer or color).
- Confirm grouping mode when asked.
- Confirm which detected units share properties.
- Confirm commercial properties (materials, finish, depth, lighting, mounting).
- Correct wrong precedents when reuse misfires.

---

## 9. System honesty

When understanding is not secure:

```text
Nu înțeleg despre ce este vorba.
Am nevoie să mă înveți.
```

Then ask the **smallest useful question**, e.g.:

- “Am detectat două layere și trei culori. Fișierul este organizat pe layere sau pe culori?”
- “Am detectat trei cuvinte. Vrei aceleași proprietăți sau grupuri separate?”

Forbidden compensations: silent continuation, approximate groups, uncertain Product Truth, pricing on unconfirmed data, badge spam, technical warning theater, confidence theater, fuzzy matching to hide ignorance.

---

## 10. Deterministic observation (external app)

Deterministic parse/geometry observation is owned by the **separate desktop analysis app**. It extracts structure and metrics and may report ambiguity signals. It must not invent commercial group identity or Product Truth.

WorkOS **consumes** a versioned external result (`artwork_analysis_contract_v1`), validates structure/provenance, and never treats observations or proposed bindings as confirmed truth. Existing in-repo SVG/DXF analyzers are LEGACY / EXTERNAL_APP_OWNED for ownership purposes — do not extend; do not delete without owner GO.

---

## 11. Artwork Understanding Assistant

**Future architectural direction — not shipped in this docs task.**

Role when built:

- Use parser observations.
- Explain what was detected.
- Identify uncertainty.
- Propose interpretations.
- Ask simple questions.
- Reuse confirmed precedents.
- Learn only under controlled policy.

AI is **not** authority and must not write Product Truth, Pricing, CostEngine, Offer, Order, Execution, or production handoff.

---

## 12. Operator confirmation

No confirmation → no Product Truth write for that interpretation. Proposals may exist transiently in session UI; they are not durable commercial truth.

---

## 13. Product Truth

Stores confirmed grouping mode, confirmed group membership/bindings, confirmed constructive/commercial properties, and provenance of confirmation (who/when) as needed for audit. Does not store unconfirmed AI guesses as truth.

---

## 14. Case memory

Confirmed situations become **case memory**: confirmation-based, versioned, auditable, immediately reusable, operator-correctable. Distinct from global model weights.

---

## 15. Controlled learning

```text
observation → AI proposal → operator confirmation → precedent saved → reuse on similar case
```

Global **model improvement** requires: clean dataset → eval → fixture tests → new version → owner GO → controlled promotion. One click must not change global system behavior.

---

## 16. Repeated-case policy

Reuse a precedent when similarity is real. Ask again only when:

- a relevant difference exists;
- the precedent does not apply;
- the case is new;
- prior explanation is insufficient.

Always say **what is different**.

---

## 17. Vector workflow

Canonical path: Desktop analysis app → external structured result (observed/proposed) → WorkOS Intake / Product System → operator review → confirm → Product Truth → quantity builder → CPP/CostEngine paths as already bounded.

Legacy in-repo SVG upload/analyze paths may still run until migration; they are not the ownership target and must not grow new analysis capability.

---

## 18. Future raster/JPG workflow

Same responsibility chain. Raster adds OCR/segmentation uncertainty — honesty contract is stricter, not looser. Out of MVP for this model doc.

---

## 19. Production decomposition boundary

Interpretation decides commercial constructive groups. Production may further decompose for CNC/nesting. Production decomposition must not silently redefine commercial Product Truth.

---

## 20. Fixture ladder

Canonical ladder (owner discussion):

1. Single layer + single color  
2. Single layer + multiple colors  
3. Multiple layers + single color  
4. Mixed / complex artwork  

**Discussed owner names (not present as repo files in this checkout):** `mi-o-culoare.svg`, `mi-2-culori.svg`, `mi-o-culoare-doua-layere.svg`, `mi-final-complex.svg` — ladder intent only.

**Found in repo (inventory only; not modified):**

| Path | Role |
|------|------|
| `fisiere-teste-svg/gradi-curat.svg` | Multi-name sample artwork |
| `fisiere-teste-svg/litere-vol-1-layer.svg` | Single-layer sample |
| `fisiere-teste-svg/litere-vol-2-layere.svg` | Two-layer sample |
| `fisiere-teste-svg/logo.svg` | Logo sample |
| `backend/tests/fixtures/intake_v6_golden_gradi/gradi-curat.svg` | Golden test SVG |
| `docs/qa/intake-v6-layer-role-template-wiring-audit-2026-07-19/runtime/gradi-curat.svg` | QA runtime copy |

Labels such as Maria / Ioana / Soare / Georgeta appearing in fixtures are **test data**, not product domain concepts.

---

## 21. Failure behavior

Uncertain → honest stop + smallest question. No silent Product Truth. No pricing continuation on unconfirmed grouping. Diagnostics may store raw observations separately from operator UI.

---

## 22. What must never be hardcoded

- Fixture filenames or display strings as domain identity  
- Detected text as permanent group identity  
- Layer names as UUID substitutes  
- Fuzzy geometric “same group” rules without confirmation  
- Auto-mix of layer and color modes  

---

## 23. UI language

Operator-facing: plain Romanian decisions (grouping mode, shared properties, confirm/correct). No internal keys, provenance dumps, confidence badges, or CPP aliases in the default path.

---

## 24. Diagnostics boundary

Raw parser dump, drift, authority internals, and unmatched keys belong in diagnostics — not as default operator chrome.

---

## 25. MVP boundary

MVP for this model (docs):

- Document contracts and honesty.
- Suspend Build 2 UI that assumes layer-only groups.
- Keep deterministic parser + existing confirmed-field authority where still valid.

MVP does **not** include shipping the AI assistant, case-memory store, or raster pipeline.

---

## 26. Future intelligence

Assisted interpretation, case memory retrieval, controlled model promotion, raster support — each under separate owner GO.

---

## 27. Build 1 impact

Build 1 is **not** fully invalid. Probably reusable: persistent UUID, confirmed properties, one-way legacy projection (while readers exist), quantity builder / CPP boundaries, placement contract, AcmPanel separation. Re-audit: meaning of `group_key`, detection source, artwork→instance mapping, orphan semantics, re-analysis, UI labels, fixture-shaped assumptions.

---

## 28. Build 2 impact

Implementation GO for operator-closure / AcmPanel composition **suspended** until grouping + assistant boundaries are owner-approved. Technical research findings (autosave, placement remint, SVG wipe, etc.) remain useful — see addendum.

---

## 29. Re-audit list

- Group definition beyond layer-only  
- `grouping_mode` persistence contract  
- Join key strategy after mode confirmation  
- Detection → proposal → confirm → instance write  
- Orphan / split-merge necessity under new model  
- LED ownership after grouping truth  
- UI chips source (confirmed groups only)  
- Case memory schema (future)  

---

## 30. Owner gates

1. Approve this teaching model as architecture direction.  
2. Approve `by_layer` / `by_color` as initial modes only.  
3. Approve honesty-stop over silent grouping.  
4. Approve AI as non-authority (future).  
5. Approve case memory vs model promotion split.  
6. Re-open Build 2 only after grouping re-audit GO.  

---

## 31. Roadmap

```text
Docs realignment (this) …………… NOW
Grouping / join re-audit ……… next owner GO
Build 2 replan ……………… after re-audit
Assistant MVP ………………… later dedicated GO
Case memory store …………… later
Model promotion pipeline …… later
Raster workflow ……………… later
```

---

## 32. Opinia sinceră

Cea mai scumpă greșeală era să construim UI pe „grup = layer = nume detectat”. Corecția corectă e disciplina: observe → ask → confirm → remember. Fără asta, Build 2 ar fi polish pe o minciună elegantă.

---

## 33. Direcție stabilită

**78/100** — responsibility chain is clear; execution waits on grouping re-audit and explicit Build 2 replan GO.
