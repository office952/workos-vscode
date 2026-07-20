# Product System P1 — Compound Engineering Shared Visual Map

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Lead | Product System UI Architect |
| Kickoff HEAD | `e52a02807722523e2292de80995d0761284e7fca` (`e52a0280`) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| P0 map (read-only) | `PRODUCT_SYSTEM_P0_SHARED_SEMANTIC_MAP.md` |
| P0 report | `PRODUCT_SYSTEM_P0_SEMANTIC_VISUAL_REALIGNMENT_FINAL_REPORT.md` |
| Mode | Visual consolidation only — **no** status/lifecycle/publication rule changes |

All agents consume this map. **Do not invent** a separate PS palette, spacing scale, card/badge/header model, Publish gate, or status semantics. P0 decisions remain locked.

---

## 1. P0 semantics (READ-ONLY — do not reopen)

| Locked item | Truth |
|-------------|--------|
| Planificat | Demoted → „În dezvoltare” secondary cluster |
| Publică fail-closed | `resolvePublishUiGate` — disabled when readiness BLOCKED |
| Proxy | Canonical BE **8000** |
| Aluminiu | Still BLOCKED / inactive |
| Action order | Salvează → Validează → Verifică → Publică |
| Status layers | Lifecycle ≠ Publication ≠ Readiness ≠ Shell roadmap |
| 10s / scores | PASS · clarity 72 · visual 68 · action 78 · status 74 · comfort **62** |

Comfort debt (P1 target): muddy translucent stacks, nested dark wells, chip/tab density, parallel hardcodes.

---

## 2. Status / action hierarchy (unchanged)

Same as P0 map §§1–3. Visual work may restyle chips/panels but must not change meaning, enablement, or layer equality.

---

## 3. WorkOS runtime reference pages (locked)

| Role | Route | Pattern extracted |
|------|-------|-------------------|
| **Form** | `/settings` | Opaque content card `bg-[#111827] border border-[#1E293B] rounded-lg p-5`; inputs `bg-[#0B1220]`; one inset well max (`#0D1321` only for form field clusters, not recursive) |
| **List / table** | `/quotes` | List rows / detail cards same opaque `#111827` + subtle `#1E293B`; no shell→card→nested→inner cascade |
| **Detail / operational** | `/intake-v6/operator` | `v6.card` = `rounded-[10px] border border-[#2A3548] bg-[#111827]`; shell `#0A0F1A`; diagnostics progressive; max one support surface |

**Stack rule:** App chrome → page content plane → **at most one** nested support surface (inset/row). Diagnostics collapsed (`details` / secondary tabs). Forbidden: shell→page→card→nested→inner→diagnostic.

---

## 4. Tokens (prefer WorkOS — map PS aliases)

Source: `frontend/src/components/workos/design-system/tokens.ts` + `docs/design/WORKOS_UI_TOKENS_DRAFT.md`.

| Role | Token / hex | PS alias |
|------|-------------|----------|
| App shell | `woSurfaces.app` `#0A0F1C` | unchanged chrome |
| Content panel L1 | `woSurfaces.surface` `#111827` + `woBorders.subtle` `#1E293B` | `PS_SURFACE_PANEL` |
| Support / raised L2 | `woSurfaces.surfaceRaised` `#1A2236` or border-only row | `PS_SURFACE_INSET` / `PS_SURFACE_ROW` |
| Input | `woSurfaces.input` `#0B1220` | `PS_SURFACE_INPUT` |
| Quiet diagnostic | slate/transparent, not deeper black | `PS_SURFACE_QUIET` |
| Strong border | `woBorders.strong` `#2A3548` | row/operational edges |

**Compatibility:** Historic PS `#0B1220` / `#0D1321` nested stacks map → L1 surface + L2 inset only. Do not introduce new hex families (no purple-hero PS theme).

---

## 5. Surface / luminance policy

1. Keep WorkOS dark shell.
2. Distinct content plane: opaque `#111827` (not `/70` mud on shell).
3. Max **one** nested support surface inside a panel.
4. Rows: prefer border + transparent/raised wash — not a third `#0A0F1A` well.
5. Diagnostics: collapsed by default; never a sixth stack level.

---

## 6. Typography / spacing / border / shadow

| Item | Policy |
|------|--------|
| Titles | `text-base`/`text-lg` font-semibold slate-100 (match Settings/Quotes density) |
| Body / helper | `text-[11px]`–`text-[12px]` slate-400/500 |
| Mono codes | secondary to human name |
| Spacing | `space-y-3`/`space-y-4`, panel `p-3`–`p-5` — no denser micro-cards |
| Radius | `rounded-lg` (WorkOS list/form); `rounded-[10px]` OK if matching Intake V6 operational |
| Shadow | none on content cards (WorkOS pages rarely shadow content) |
| Badge | StatusBadge / semantic tones only; no badge soup; catalog chip in `<details>` |
| Warning | amber/rose border wash — one banner, not nested warning cards |
| Tabs | Primary authoring tabs; diagnostic cluster demoted/collapsed |
| Form controls | `PS_SURFACE_INPUT` + strong border; focus sky/blue like WorkOS |
| Empty | plain muted text — no empty-state nested card |

---

## 7. Routes in scope

| Route | Visual role |
|-------|-------------|
| `/product-system/products` | Catalog list plane |
| `/product-system/products/:code` | Detail / authoring |
| `/product-system/blueprint-dossier` | Dossier sticky actions (fail-closed Publică preserved) |
| `/product-system/{planned}` | Placeholder — demoted chrome only |

---

## 8. Figma

| Item | Value |
|------|-------|
| File | `0CDPIuqoaZ1OQgNnvNyl1F` |
| Observed 2026-07-21 | Top-level page **00 — Cover & Index** = Intake V6 operational redesign — **not** PS Authoring Studio |
| Class | **OUT_OF_SCOPE / NEEDS_OWNER** for PS sync — do not invent PS frames; no FINAL |
| Authority for P1 | WorkOS runtime refs (§3), not this Figma file |

---

## 9. Screenshots / a11y

| Pack | Content |
|------|---------|
| Before | P0 `ui-truth-audit/after/` + P1 `p1-visual/before/` if captured |
| After | `p1-visual/after/`: landing, VL detail, composition, readiness, publication fail-closed, runtime, WorkOS refs (`/settings`, `/quotes`, `/intake-v6/operator`), Figma classify |
| A11y | tab roles, expand/collapse `aria-expanded`, focus visible on primary actions, contrast preserved on opaque surfaces |

---

## 10. Allowlist (touch only)

- `productSystemSurfaces.ts` (+ tests if any)
- `ProductSystemLayout.tsx`, `ProductSystemPlannedSectionPage.tsx`
- `ProductSystemTemplateDetailPanel.tsx`, `TemplateDualStatusChips.tsx`
- `TemplateCompositionAuthoringPanel.tsx`, `ComponentContractUsedByPanel.tsx`
- `ProductE2EReadinessPanel.tsx`, `ProductTemplatePublicationPanel.tsx`, `TemplateRuntimePreviewPanel.tsx`
- Dossier-adjacent presentation: `FinishMountingOwnershipPanel.tsx`, `LegacyReplacementReadinessPanel.tsx`, `TemplateLifecycleReadinessPanel.tsx`, `pages/BlueprintDossierStudio.tsx` (visual only)
- Catalog comfort (surfaces only): `TemplateLibraryView.tsx` / `ProductSystemUnifiedCatalog.tsx` / `ProductSystemCanonicalCatalog.tsx` as needed
- FE tests under `frontend/src/features/product-system/*`
- Docs: this map, final report, living worklog, screenshot evidence

**Forbidden touch:** CostEngine, Pricing rates, Inventory-as-price, Product Truth compilers/snapshots, schema/migrations, Aluminiu activation, SVG/DWG/DXF, desktop transport, mobile, BE publication rules, dirty-tree unrelated files.

---

## 11. Agents (after CP0 freeze)

| Agent | Focus |
|-------|--------|
| A | WorkOS reference analysis (locked above) |
| B | Surface / luminance |
| C | Layout / density |
| D | Typography / controls |
| E | Readiness / publication / runtime panels (**visual only**) |
| F | Figma classify / optional sync |
| G | QA / screenshots / a11y |

---

## 12. Checkpoints CP0–CP5

| CP | Meaning |
|----|---------|
| **CP0** | This visual map frozen + allowlist |
| **CP1** | Surfaces / layout aligned to WorkOS tokens |
| **CP2** | Composition + dossier presentation simplified (**P0 semantics preserved**) |
| **CP3** | Readiness / publication / runtime visual alignment (**fail-closed preserved**) |
| **CP4** | Tests + screenshot matrix |
| **CP5** | Worklog (P0 pointer + P1) + final report + allowlist commits |

---

## 13. Commits (allowlist messages)

1. `refactor(product-system-ui): align surfaces and layout with WorkOS`
2. `refactor(product-system-ui): simplify template composition and dossier presentation`
3. `refactor(product-system-ui): align readiness publication and runtime panels`
4. `test(product-system-ui): preserve semantic and interaction coverage`
5. `docs(qa): add P0 pointer and P1 visual acceptance evidence`

---

## 14. PASS / stop

**PASS** requires: P0 intact, Publică fail-closed, proxy 8000, material WorkOS alignment, reduced nesting/badges, comfort improved vs 62, screenshots/a11y/tests, Aluminiu blocked.

**Stop** only if: business rules/schema/lifecycle-publication change needed; insufficient WorkOS tokens needing design-system owner decision; inseparable dirty tree; Figma fundamentally different flow.
