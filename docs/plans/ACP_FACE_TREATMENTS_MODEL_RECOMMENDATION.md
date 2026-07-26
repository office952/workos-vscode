# Recommendation — ACP face treatments model

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_FINALIZE_BLUEPRINT_AUDIT_AND_AUDIT_ACP_COMPOSABLE_FACE_SYSTEM` |
| Status | **RECOMMENDATION ONLY** — awaiting owner review |
| Owner rule | `ACP_FACE_TREATMENTS_MUST_BE_COMPOSABLE_NOT_EXCLUSIVE` |

---

## Single recommendation

### Option 4 — FIX AUTHORITY / PERSISTENCE CONFLICT FIRST

Before implementing composable face treatments, unify **what ACP product is** and **how SVG→component→FinishSetup→PD** stores multiple face treatments.

**First failing boundary (must fix first):**

```text
Product System SVG component-binding contract
+ FinishSetup persistence
```

Missing today: cutout / routed-face / acrylic-insert roles; zone identity; any `face_treatments[]` / `visual_zones[]`. Present: `SUPPORT_CONTOUR` MAX_ONE + letter/logo as **other products**.

---

## Why not Options 1–3 as the first move

| Option | Why not first |
|--------|----------------|
| **1 EXTEND EXISTING ACP COMPONENT WITH COMPOSABLE FACE TREATMENTS** | Correct long-term shape candidate, but extending `TPL-ACM-BOXED…` while `TPL-ACP-LIGHT-ROUTED` still owns routed/LED/insert as a parallel product deepens the fork. |
| **2 ACP BASE + LOCAL FACE MODULES** | Best **follow-on** after authority cleanup — matches bindable-component pattern. Premature now. |
| **3 DISTINCT ACP PRODUCT VARIANTS** | Recreates exclusive `face_mode`; fights owner mixed-face rule. |

---

## What to keep / adapt / not build

| Keep | Adapt | Do not build |
|------|-------|--------------|
| Live `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` as shell authority for V6 | Binding vocabulary to attach **treatments** to one shell | Exclusive global `face_mode` products |
| Letters as related product/instances (applied) | Relation model: letters **on** ACP zone, not XOR | React Flow Blueprint canvas |
| Internal frame + fixing as separate shell configs | Keep separate from face treatments | Dossier JSON as BOM/task SoT |
| Structural RO / lifecycle gates | Extend readiness **per zone** later | Parallel task catalog from Dossier |
| Dossier Studio patterns (groups, banners, readiness) | Port into Product System **admin UI** (Option 2 Blueprint reuse) | New pricing/CPP in this GO |

---

## Dossier UI reuse (accepted Blueprint Option 2)

| Pattern | Use for ACP |
|---------|-------------|
| Authority-labeled section groups | Shell / Face treatments / Illumination / Docs |
| Variants | Construction only (thickness, fold) — not exclusive face modes |
| Readiness / validation summary | Per shell + per zone later |
| Active/archive + version | Template / dossier lifecycle |
| task_rules editor | Documentation hint only |

Contracts remain authority. UI remains surface.

---

## Canonical authority (target after Option 4)

```text
Product System contracts (one ACP shell + face treatment modules/roles)
→ FinishSetup (shell + face_treatments[] with geometry provenance)
→ ProductDefinition
→ ProductAggregate
→ CPP (owner-gated)
→ Snapshot
→ existing tasking
→ Execution
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| Implementing zones on wrong product fork | Resolve ACM boxed vs LIGHT-ROUTED vs CASSETTED first |
| Treating letters as only ACP treatment | Keep letters identity; add **relation** to zone |
| Finish enum swallowing treatments | Keep finish ≠ treatment ≠ material ≠ geometry role |
| BE stale hiding persistence bugs | Restart BE before any implementation E2E |
| Nostalgia Blueprint canvas | Already disproven — do not invent |

---

## Owner gates before implementation

1. Accept Option 4 as first step (or override with written rationale).
2. Nominate **one** live ACP product authority for V6 composition (recommend keep ACM boxed as shell).
3. Decide fate of `TPL-ACP-LIGHT-ROUTED` knowledge: migrate into face modules vs remain QuoteWizard-only legacy.
4. Confirm no exclusive `face_mode` variants.
5. Confirm Dossier remains documentation admin.

---

## First recommended build (after GO)

**Authority + persistence contract for composable face treatments** (roles, FinishSetup shape, PD projection rules) — still no CPP/tasking/Execution.

Then: **Option 2 implementation** (ACP base + local face modules) with Dossier-inspired Product System admin UI.

---

## Next safe step (single)

**FIX ACP AUTHORITY CONFLICT FIRST**

(Equivalent owner token: stop for review, then GO authority/persistence build — not full face UI yet.)
