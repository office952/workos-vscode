# Bond Second Product — Registry Identity Inventory (STOP)

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `1b1b333c` |
| Live DB evidence | `runtime/bond_second_product_registry_inventory.json` |
| Verdict | **STOP — multiple near-identities; no create** |

---

## 1. Target (owner brief)

Bond / ACM casetat **cu** litere sau logo volumetric — vertical slice, one representative variant, root composes, reuse VL letter/logo templates, frame optional/conditional, no CAD, no publish.

---

## 2. Near-identity scan (Bond / ACM / ACP / casetat)

| Code / string | Kind | Live DB | Role today | Duplicate risk |
|---------------|------|---------|------------|----------------|
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | Product Template | **active**, `publication_status=NULL` | Dual: standalone root + VL optional child; owner label „Panou Alucobond casetat” | **Canonical live Bond/ACM casetat** |
| `TPL-ACM-CASSETTED-PANEL` | Product Template | inactive | Future cassette candidate; `owner_go_required`; not Intake child | Twin of boxed — do not activate as parallel |
| `TPL-ACP-LIGHT-ROUTED` | Product Template | inactive | PARALLEL_LEGACY_COST_PATH illuminated ACP | Not composition SoT |
| `TPL-BOND-CASETAT` | String-only legacy | **not a PT row** | Deprecated mapping → ACM boxed; forbidden for new selection | Must not revive |
| `TPL-CUT-ACM-LETTERS` | Product Template | inactive | Cut-ACM letters adjacent name | Near-name noise; not Bond composite |
| UI „Panou ACP casetat” / „Alucobond casetat” / „Bond” | Labels | — | Shop synonyms for ACM boxed | Terminology only |

**Decision already on file:** `docs/decisions/TPL_BOND_CASETAT_LEGACY_STATUS.md` + `ACP_ACM_DIBOND_TERMINOLOGY_MAP.md` — live authority for the **panel** is `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`.

---

## 3. Letters / logo identities (reuse candidates)

| Code | Live | Usage policy | Notes |
|------|------|--------------|-------|
| `TPL-VOLUMETRIC-LETTERS_v2` | active | root_offerable | First real product; **already links ACM boxed as optional_addon** |
| FACE/BACK/LED/FINISH/ALUMINIU | active (Aluminiu active unpublished per VL closure) | component_only | Letter truth owners — reuse, do not copy into Bond root |
| `TPL-VOLUMETRIC-LOGO_v1` | active row | candidate / root blocked pending GO | Has 6 logo child modules; **no link to ACM boxed** |
| Logo FACE/RETURN/BACK/LIGHTING/FINISH/MOUNTING | active | component_only | Reuse candidates if logo variant chosen |

---

## 4. Frame identity

| Surface | Identity | Product Template? |
|---------|----------|-------------------|
| ACP internal frame | domain `acp_internal_frame` on ACM boxed shell | **No** — config/domain, not a PT |
| Metal premount | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | Yes — VL optional; alternate support path |
| Fastening profiles | mounting fastening registry | Not frame PT |

**Implication:** frame is conditional domain on Bond/ACM, not a separate product root. Operator-explicit include/exclude required if production rules unclear (stop condition).

---

## 5. Composition graph (live)

```text
TPL-VOLUMETRIC-LETTERS_v2  (root)
  ├─ required → FACE, BACK, ALUMINIU, LED, FINISH
  ├─ optional → TPL-METAL-PREMOUNT-STRUCTURE_v1
  └─ optional → TPL-ACM-BOXED-MOUNTING-SUPPORT_v1   ← Bond panel as child

TPL-ACM-BOXED-MOUNTING-SUPPORT_v1  (standalone root, dual-role)
  └─ (no children linking letters or logo today)

TPL-VOLUMETRIC-LOGO_v1
  └─ required → logo FACE/RETURN/BACK/LIGHTING/FINISH/MOUNTING
  └─ (no ACM / Bond link)
```

**Missing product shape:** Bond/ACM as **root** composing letters **or** logo as children (inverse of VL). That is the only gap that is *not* already a near-duplicate panel identity.

---

## 6. Why STOP (hard)

Owner brief stop condition: *ambiguous/duplicate identity → STOP before create → inventory → propose canonical → no duplicates.*

Creating any of the following without an owner pick would violate that:

1. New `TPL-BOND-*` / `TPL-ACM-*` panel twin next to live ACM boxed  
2. Activating `TPL-ACM-CASSETTED-PANEL` as the second product  
3. Reviving `TPL-BOND-CASETAT`  
4. Treating VL+optional ACM as a *new* product without naming the composite distinctly

---

## 7. Proposed canonical (owner must pick one)

### Option A — Prefer (smallest coherent, no new panel identity)

| Field | Proposal |
|-------|----------|
| Bond panel identity | **Reuse** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` (do not create twin) |
| Second-product meaning | Configure ACM boxed **composition**: optional/conditional **letters pack reuse** *or* **logo pack reuse** (one primary variant) |
| Letters identity | Reuse `TPL-VOLUMETRIC-LETTERS_v2` children (FACE…FINISH / Aluminiu) — **not** copy PT |
| Logo identity | Reuse `TPL-VOLUMETRIC-LOGO_v1` children if logo variant chosen |
| Frame | Keep `acp_internal_frame` domain; **operator-explicit** optional/conditional |
| Family | Keep `panouri_acp_iluminate` / Panouri ACP / ACM |
| Publish | KEEP_DRAFT — no publish |

**Risk:** ACM boxed is already a live dual-role product; “second real product” becomes a **composition extension**, not a greenfield PT. Must document vs VL inversion clearly.

### Option B — New composite root (only if owner wants distinct catalog SKU)

| Field | Proposal |
|-------|----------|
| New root code | e.g. `TPL-ACM-BOXED-WITH-VOLUMETRIC_v1` (name TBD by owner) |
| Bond panel | Still **child/reuse** of `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` — never a third panel |
| Letters/logo | Linked children by reuse |
| Forbidden | New panel formula twin; activating CASSETTED-PANEL; BOND-CASETAT |

**Risk:** catalog proliferation; generalization cost vs VL.

### Option C — Decline second product; keep draft as documentation only

Declare that **VL root + optional ACM** already covers “litere pe Bond casetat” commercially/compositionally; do not invert until a real shop SKU requires Bond-as-root.

---

## 8. Owner decision required (exactly one)

1. **A** — Extend ACM boxed composition (recommended)  
2. **B** — New composite root code (owner supplies display name + code)  
3. **C** — No second product; keep inventory only  

Also freeze before implement (after choice):

- Primary variant: **letters** XOR **logo** (not both in v1)  
- Frame: required / optional / conditional + trigger  
- Commercial basis: reuse ACM boxed + VL/logo registry mappings only — if new formula needed → separate STOP with ≤2 options  

---

## 9. Forbidden confirmations

- Did **not** create a new Bond/ACM panel template  
- Did **not** publish / activate inactive twins  
- Did **not** further deep-dive VL beyond worklog closure pointer  
- Dirty tree left untouched outside allowlist docs  
