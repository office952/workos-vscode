# WORKOS_ACM_PANEL_NAMING_OWNERSHIP_ASSEMBLY_AND_INVENTORY_BINDING_V1

| Field | Value |
|-------|--------|
| Status | **IMPLEMENTED — awaiting owner review** |
| Mode | Slice A+B implemented — see audit report |
| Date | 2026-07-20 |
| Branch baseline | `feature/product-system-active-path-isolation-v1` @ `b36bad9` (or HEAD after audit commit if stamped) |
| Prerequisite audits | Blueprint L1-P PASS · Downstream readiness audit · Amendament operation truth (§39–§50) |
| Canonical fixture | `IV6-DB2F86B7` / `a7b0162b-dc91-467f-aa24-c1279fb3a073` |
| Combines | Slice A (naming/ownership) + Slice B (assembly + inventory binding + PD parity) |

---

## 0. Locked owner decisions (plan assumptions)

These are treated as **decided for this plan** from prior owner GO / amendment / audit recommendations. Owner may veto at gate §18 before code.

| # | Decision | Locked value |
|---|----------|--------------|
| D1 | Fixture commercial posture | Estimate OK; **final Offer/Exec NO** until confirmations |
| D2 | Multi-panel overall | **Assembly extent** (panel bounds / coherent `assembly_dimensions`); **never** single-contour `geometry.width_mm` as overall when `panels.length > 1` |
| D3 | Slice order | **A+B this build**; C pricing preview later; D Exec later |
| D4 | Hourly commercial | **Forbidden** for ACM commercial lines (keep EUR/mp · EUR/ml · EUR/set) |
| D5 | Operation SoT | Atelier: **MIXED** · Cadru: **OWNER_RULES** · Runtime seed: **partial adapter** (do not invent new DAG) |
| D6 | `PROFILE-SHS-20X20X1_5` | **Fixing only** — **not** ACM/ACP internal frame default |
| D7 | A+B vs Execution | **No** task materialization, no ops/task templates new, no DAG copy into Pricing/Blueprint |
| D8 | PD ACM-root + Letters workspace | **In scope for parity** — AcmPanel truth must be observable when querying ACM root with same `workspace_id` (today: `template_only` empty) |
| D9 | Material codes | **No CostEngine code renames**; canonical **display/binding** → `MAT-ACM-BOND-*`; aliases/legacy documented |
| D10 | Blueprint L1-P | **Untouched** (read-only projection already correct for assembly) |

---

## 1. Scope

### In scope

1. **Naming alignment** — canonical labels + honesty notes for ACM/ACP/Bond/Dibond/Alucobond; face-litere PMMA trap; envelope vs assembly vocabulary.
2. **Ownership matrix** — who owns geometry, construction, material SKU, rates, ops DAG pointers; document-only + code comments/contracts where needed.
3. **Assembly extent** — single shared derivation used by quote_input / PD projection / Aggregate consumers for multi-panel (same algorithm as Blueprint L1-P).
4. **ProductDefinition parity** — Letters root keeps proposal gating; ACM root + workspace projects AcmPanel truth (or explicit linked-child read) instead of empty `template_only`.
5. **ProductAggregate alignment** — nested panels remain children; no segment-as-product; consume assembly dimensions consistently.
6. **Inventory binding** — template/BOM resolves to canonical ACM panel SKU; thickness alias path clarified; no silent `MAT-ACP-FATA-LITERE` as shell face.
7. **Alias/legacy strategy** — keep codes; mark duplicates; prefer `MAT-ACM-BOND-3MM` for shell.
8. **Operation SoT pointers** — docs + seed comments only; no new operations.
9. **Tests + runtime proof + screenshots + worklog/QA** for this build only.

### Out of scope

- Pricing preview UI / new commercial formulas (Slice C)
- Offer/Order writes, reprice changes
- Execution Plan / task materialization / drag-and-drop
- Unifying MIXED §4 CNC order with seed `task_rules` (future owner GO)
- Blueprint changes, SvgAnalyzer write core, Fundal write path
- DB migrations, mass inventory seed rewrite, material code renames
- Firmă luminoasă / totem / MULTI / Employee Mobile
- Foil/Oracal shell task_rules materialization

---

## 2. Surse de adevăr (read order)

| Priority | Source | Use for |
|----------|--------|---------|
| 1 | Runtime fixture `IV6-DB2F86B7` | Proof assembly 2000×350 vs envelope 1000 |
| 2 | `acm_panel_instance` + `field_authority` + segmented | Component truth |
| 3 | Blueprint L1-P read model algorithm | Assembly extent reference (do not regress) |
| 4 | [`MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md`](../architecture/MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md) | Operation / finish workshop SoT |
| 5 | [`ACP_INTERNAL_FRAME_OWNER_RULES.md`](../decisions/ACP_INTERNAL_FRAME_OWNER_RULES.md) | Frame formula; L2≠frame; ribs; no 20×20 frame default |
| 6 | [`ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md`](../architecture/ALUCOBOND_CASED_PANEL_SVG_CONFIGURATION.md) | L1/L2/blank mapping |
| 7 | [`ACP_ACM_DIBOND_TERMINOLOGY_MAP.md`](../architecture/ACP_ACM_DIBOND_TERMINOLOGY_MAP.md) | Naming family |
| 8 | [`MATERIAL_CANONICAL_NAMING_AND_ALIASES.md`](../architecture/MATERIAL_CANONICAL_NAMING_AND_ALIASES.md) + `material_canonical_naming.py` | Inventory naming |
| 9 | [`MOUNTING_FIXING_SYSTEM_CONTRACT.md`](../architecture/MOUNTING_FIXING_SYSTEM_CONTRACT.md) | PROFILE-SHS-20X20X1_5 fixing |
| 10 | Downstream audit + Amendament §39–§50 | Gates, duplicates, A+B boundaries |
| 11 | Seeds `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | BOM/ops codes (adapter, not atelier bible) |
| 12 | Pricing registry | Consumer only — do not become ownership SoT |

---

## 3. Naming decision

| Concept | Canonical (operator / system) | Aliases OK | Forbidden / honesty |
|---------|-------------------------------|------------|---------------------|
| Component | **AcmPanel** / „Panou Alucobond casetat” | ACP casetat, Bond (conversational) | New template ID „Bond” |
| Material shell | **Panou compozit aluminiu (ACM/ACP)** | Alucobond, Dibond, bond | Confuse with plexi face |
| SKU 3 mm shell | **`MAT-ACM-BOND-3MM`** (preferred) | `MAT-ACP-3MM` legacy parallel | Silent dual-pricing without note |
| SKU resolver | `MAT-ACM-BOND-PANEL` → 3MM/4MM | — | Use as face letter material |
| Letter face | **PMMA/plexi** via `MAT-ACP-FATA-LITERE` | — | Treating as ACM panel |
| Envelope dim | „contur / panel envelope” | — | „ansamblu” when multi-panel |
| Assembly dim | „ansamblu / assembly extent” | — | Using envelope as overall |
| L1 / L2 | întoarcere / buză spate | return / rear lip | L2 changes frame size |
| Ops | V-groove (repo term) | V-cut conversational | Pricing owns order |

**Deliverable artifacts (implementation phase):** update naming map pointers + inventory `source_notes` consistency; FE/BE operator strings where misleading; **no** code renames of CostEngine keys.

---

## 4. Ownership matrix

| Concern | Owner | Consumer | Must not own |
|---------|-------|----------|--------------|
| Panel/assembly geometry mm | AcmPanel instance + segmented confirm | Blueprint, PD, quote_input | Pricing UI |
| Construction l1/l2/thickness authority | `field_authority` on instance | PD casing keys, estimate gates | Catalog silent final |
| Frame size formula | `ACP_INTERNAL_FRAME_OWNER_RULES` + `acp_internal_frame_domain` | PD when frame active | Pricing, Blueprint |
| Workshop CNC/foil order | **MIXED** (docs) | Future Exec (not A+B) | Seed as sole SoT; Pricing; Blueprint |
| Runtime task_rules coarse | Template seed (adapter) | Exec later | Replacing MIXED |
| Material purchase SKU | Inventory + canonical naming | Pricing registry, BOM | Product Template inventing SKU |
| Commercial unit rates | Pricing Registry / CPP | Offer | Operation order |
| Composition membership | Product composition + instance `composition_status` | PD honesty | Technical confirm alone |
| Fixing 20×20×1.5 | Fixing system contract | Montaj fixing UI | Internal frame default |

---

## 5. Assembly extent

### Algorithm (must match Blueprint L1-P)

```text
If panels.length > 1:
  minX = min(p.x); maxX = max(p.x + p.width)
  minY = min(p.y); maxY = max(p.y + p.height)
  extentW, extentH = maxX-minX, maxY-minY
  If assembly_dimensions within tol (1 mm): may adopt; else extent + warning
  NEVER use geometry.width_mm/height_mm as overall
Else:
  single panel W×H or coherent assembly_dimensions
```

### Implementation target

- Extract **shared pure helper** (prefer FE already in `blueprintReadModel` + BE mirror in `acm_quote_input_helpers` or small shared module used by PD/quote path).
- Wire `derive_acm_casetted_quote_input` / config hydration to prefer:
  - multi-panel assembly W×H for `panel_width_mm`/`panel_height_mm` **commercial overall**, OR
  - introduce explicit keys `assembly_width_mm` / `assembly_height_mm` while keeping per-panel dims — **choose one in implementation; default plan: explicit assembly keys + derived area/perimeter from assembly**, with warning if envelope ≠ assembly.
- Fixture expected: **2000 × 350**, not 1000 × 350.

**Default choice for this plan:** add/propagate `assembly_width_mm` / `assembly_height_mm` (and area/perimeter from assembly) without deleting per-panel geometry; quote commercial area uses assembly when multi-panel.

---

## 6. ProductDefinition parity

| Path | Today | Target |
|------|-------|--------|
| `TPL-VOLUMETRIC-LETTERS_v2` + WS | Projects `acm_panel_instance`, `segmented_background_proposal` (2000×350), technical_confirmed=false | **Preserve**; add assembly extent keys if missing |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` + same WS | `template_only`, empty canonical, missing dims | **Parity:** load workspace finish_setup AcmPanel (coalesce) into canonical_values even when root template is ACM; mark provenance `workspace_payload` / linked |
| Segmented PROPOSED | proposal only, `downstream_effects=false` | **Unchanged** |
| Segmented CONFIRMED | confirmed key | **Unchanged** |
| field_authority | projected | **Preserve**; never upgrade catalog→confirmed |

---

## 7. ProductAggregate alignment

- AcmPanel = one component; panels = nested children (not products).
- Aggregate must not invent `positioned_on` confirmed from unknown.
- When consuming dimensions for cost projection, use **assembly extent** for multi-panel.
- Segmented aggregate projection remains CONFIRMED-only / INFORMATIONAL_ONLY for tasks — **no materialization**.

---

## 8. Canonical Inventory material

| Role | Canonical code | Notes |
|------|----------------|-------|
| Shell face/returns material | `MAT-ACM-BOND-PANEL` → resolve `MAT-ACM-BOND-3MM` (default) / `4MM` | Template BOM already points at PANEL |
| Preferred priced SKU | `MAT-ACM-BOND-3MM` | Owner-confirmed 15 EUR/mp |
| Legacy duplicate | `MAT-ACP-3MM` | Same generic panel — **alias/legacy**; do not delete in A+B; document prefer BOND |
| Not shell | `MAT-ACP-FATA-LITERE` | PMMA letters — honesty notes only |
| Fasteners | `MAT-SURUBURI-GEN` | Unchanged |

Binding work: ensure ACM boxed material roles and rate resolver prefer BOND path; UI/registry notes already warn — tighten references that still imply ACP-3MM as shell SoT.

---

## 9. Alias / legacy strategy

| Item | Strategy in A+B |
|------|-----------------|
| `MAT-ACP-3MM` | Keep code; mark legacy duplicate of BOND-3MM; no migration delete |
| `MAT-ACP-FATA-LITERE` | Keep code; strengthen „nu e panou ACM” in notes/UI copy where touched |
| `TPL-BOND-CASETAT` | Leave deprecated — do not reactivate |
| `TPL-ACM-CASSETTED-PANEL` | Leave inactive candidate — out of scope |
| Conversational Bond/Alucobond | Allowed in labels via terminology map |
| CostEngine codes | **Frozen** — rename forbidden |

---

## 10. Operation SoT pointer

| Concern | Pointer (document only in A+B) |
|---------|--------------------------------|
| CNC workshop order | MIXED §4 |
| Foil after body | MIXED §5 |
| Print prep early / apply late | MIXED §7 |
| Frame formula / L2 independence | OWNER_RULES |
| Ribs 1000/750 | OWNER_RULES |
| Runtime coarse tasks | seed `task_rules` — **adapter**, conflict vs MIXED noted |
| Pricing rates | Registry — **consumer**, not order owner |

Add short cross-links in worklog + optionally a 1-pager under `docs/architecture/product-system/` pointing to MIXED/OWNER_RULES — **no** new operation list invented.

---

## 11. Conflict SoT vs runtime

| Conflict | Plan action |
|----------|-------------|
| MIXED CNC (V-opus → cutout → outer → fold) vs seed cut→V→fold | **Document only**; do not change seed sequences in A+B |
| Foil-after missing from task_rules | **Document gap**; no materialization |
| Envelope 1000 vs assembly 2000 in quote_input | **Fix** via assembly extent (core of B) |
| PD ACM-root empty | **Fix** parity |
| Triple tariff stores (CPP/WC/inventory) | **Do not unify prices** in A+B; only naming/binding |
| Frame clearance 5 mm legacy | Leave GUARDED; do not resurrect |

---

## 12. PROFILE-SHS-20X20X1_5 rule

| Context | Rule |
|---------|------|
| Internal ACM/ACP frame | **Not allowed** as default profile (`not_for: acp_internal_frame`; accepted_profile_codes empty) |
| Vertical steel fixing | **OWNER_CONFIRMED** for `FIXING-SYSTEM-VERTICAL-STEEL-BRACKET` |
| MIXED §6 20×20 example | Didactic cutlist topology only |
| A+B code | Add/verify comments + tests that frame path does not auto-select SHS 20×20; no UI change required unless a false default exists |

---

## 13. No duplicate truth

| Action | Allowed | Forbidden |
|--------|---------|-----------|
| Point docs to MIXED/OWNER_RULES | Yes | Copy full DAG into Pricing/Blueprint/PD |
| Share assembly helper FE↔BE | Yes | Second conflicting formula |
| Prefer MAT-ACM-BOND-3MM | Yes | Create third SKU |
| Keep seed task_rules | Yes | Rewrite production order |
| Honesty labels envelope≠assembly | Yes | Silent overwrite without warning |

---

## 14. Implementation units (when GO)

### U1 — Shared assembly extent helper

- Pure function: panels → extent + optional assembly_dimensions compare + warnings.
- Unit tests: 1000+1000→2000; envelope ignored; offset normalize; tol 1 mm; single panel.

### U2 — Quote input / commercial geometry binding

- `acm_quote_input_helpers` (+ callers) use assembly for multi-panel area/perimeter.
- Tests: fixture-like payload → area from 2000×350 not 1000×350.

### U3 — ProductDefinition parity

- ACM root + workspace_id projects coalesced `acm_panel_instance` + segmented proposal/confirmed gates unchanged.
- Tests: pytest PD ACM-root+WS; Letters path regression.

### U4 — Aggregate / composition consumers

- Any dimension read for ACM multi-panel uses assembly keys.
- No segment product rows.

### U5 — Inventory / naming honesty

- Canonical naming notes + any resolver preference for BOND-3MM.
- Guard: shell BOM ≠ `MAT-ACP-FATA-LITERE`.
- Docs: terminology + material aliases pointers.

### U6 — Operation SoT pointer doc

- Short architecture note: SoT pointers + seed conflict + A+B non-goals.
- Cross-link from worklog.

### U7 — PROFILE / frame non-default guard

- Test or assertion: internal frame path does not accept SHS 20×20 as default.

### U8 — QA pack

- Worklog + `docs/qa/BUILD_…` or audit addendum; runtime proof; screenshots.

**Suggested commit:** one coherent commit (or max two: code+tests / docs+evidence).

---

## 15. Tests

| Area | Cases |
|------|-------|
| Assembly extent | multi 2000; envelope ignored; mismatch warning; single panel; L1-B invalid panels |
| Quote input | area/perimeter from assembly; fold_length uses assembly sides when multi |
| PD Letters | regression: proposal 2000; no confirmed leak |
| PD ACM root + WS | non-empty instance; assembly keys; statuses preserved |
| Coalesce | resolveInstance order unchanged |
| Material binding | PANEL→3MM; not FATA-LITERE for shell |
| Frame | fold_count ignored; SHS 20×20 not frame default |
| Naming | notes/aliases present (unit on naming map if touched) |
| Regression | blueprintReadModel 2000; acm panel coalesce; segmented gates; CPP non-hourly untouched |

---

## 16. Runtime proof

Fixture `IV6-DB2F86B7`:

| Check | Expected |
|-------|----------|
| Blueprint L1-P | still 2000×350, L1-P, 0 PUT on preview |
| Letters PD | proposal assembly 2000×350; envelope 1000 visible but not overall |
| ACM-root PD + WS | **after fix:** instance present; assembly extent 2000×350 |
| Quote dry-run / derive (read-only) | area reflects 2000×350 when multi-panel |
| Inventory/Pricing | BOND-3MM still listed; no hourly; no DAG in Pricing |
| Zero writes | proof script: no PUT on PD GET / inventory browse |

---

## 17. Screenshots

Evidence dir (implementation phase):  
`docs/audits/_evidence/2026-07-20_acm-panel-naming-ownership-assembly-binding/`

Minimum:

1. Intake AcmPanel + Blueprint collapsed (2000×350)  
2. Blueprint expanded assembly  
3. Letters PD observability (API extract OK)  
4. ACM-root PD after parity (API/UI)  
5. Inventory ACM search (BOND-3MM)  
6. Pricing ACM template coverage (consumer only)  
7. Composition inconsistency honesty still visible  
8. Full-page Configurare scroll  

---

## 18. Risks

| Risk | Mitigation |
|------|------------|
| Changing `panel_width_mm` meaning breaks single-panel offers | Prefer explicit `assembly_*` keys; keep panel_* as envelope/primary panel where needed |
| Dual FE/BE formula drift | Shared algorithm tests both sides |
| Accidental seed DAG rewrite | Code review boundary; no task_rules edits |
| Silent material migration | Alias only; no deletes |
| Pricing treated as fixed by this build | Out of scope Slice C |
| PD parity loads wrong template payload | Coalesce via existing resolve order; provenance notes |

---

## 19. Commit strategy

| Preference | One commit |
|------------|------------|
| Message sketch | `fix(intake-v6): AcmPanel assembly extent + naming/inventory binding` |
| Max | 2 (code/tests · docs/evidence) |
| Include | helper, quote/PD wiring, tests, worklog, QA, evidence |
| Exclude | unrelated dirty tree files; `.venv`; logs; unrelated docs |

---

## 20. Boundaries (hard)

- No new operations / task templates  
- No Execution activation / materialize  
- No Pricing formula invention / hourly commercial  
- No Blueprint feature work  
- No SvgAnalyzer write changes  
- No Offer/Order/Inventory stock writes  
- No DB migrations / mass seed renames  
- No copy of MIXED DAG into Pricing or Blueprint  
- No inventing 20×20 as frame default  

---

## 21. Owner gates (STOP — approve before code)

Approve or amend:

1. **GO** this plan as Slice A+B combined build?  
2. Confirm **explicit `assembly_width_mm` / `assembly_height_mm`** (vs overloading `panel_width_mm`)? **Plan default: explicit assembly keys.**  
3. Confirm **PD ACM-root parity** in scope (D8)?  
4. Confirm **no seed task_rules changes** even to “fix” MIXED order?  
5. Confirm canonical SKU preference **`MAT-ACM-BOND-3MM`** with `MAT-ACP-3MM` legacy retained?  
6. Confirm **PROFILE-SHS-20X20X1_5** fixing-only rule as documented?  
7. Any additional naming strings that must change in Intake UI in A+B?

---

## 22. Definition of Done (post-GO)

- [ ] Assembly extent shared + tests green (2000 on fixture path)  
- [ ] Quote/PD/Agg consumers do not use envelope as multi-panel overall  
- [ ] PD ACM-root + WS shows AcmPanel projection  
- [ ] Naming/inventory honesty for BOND vs ACP-face  
- [ ] Operation SoT pointer doc; no DAG duplication  
- [ ] SHS 20×20 not frame default (guard/test)  
- [ ] Runtime proof + screenshots  
- [ ] Worklog + QA report  
- [ ] Commit hash reported  
- [ ] **STOP** for owner review (no Slice C)

---

## 23. Files likely touched (preview — not exhaustive)

| Area | Candidates |
|------|------------|
| FE | `acmPanel/blueprintReadModel.ts` (export helper), possible `assemblyExtent.ts` |
| BE | `acm_quote_input_helpers.py`, `product_definition_builder_service.py`, maybe `acm_bond_material_rate_resolver.py` |
| Naming | `material_canonical_naming.py`, terminology docs |
| Docs | worklog, QA BUILD, short SoT pointer, this plan (status→executing when GO) |
| Tests | new + regression acm/pd/blueprint/quote |

---

## Owner gate

**STOP after plan.** No implementation until explicit GO on §21.
)
