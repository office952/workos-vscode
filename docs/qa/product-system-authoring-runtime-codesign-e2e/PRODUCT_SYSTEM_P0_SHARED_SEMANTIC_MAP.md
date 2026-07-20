# Product System P0 — Compound Engineering Shared Map

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Lead | Product System UI Architect |
| HEAD (kickoff) | `033f28fee016752622debba4f5a1817303d9a1ef` |
| Source of truth | `PRODUCT_SYSTEM_FULL_PAGE_UI_TRUTH_AUDIT.md` |
| Mode | Presentation / mapping only — no architecture reopen |

All agents consume this map. **Do not invent** new status/lifecycle/color/nav/publication/backend authority. Map changes need Lead review.

---

## 1. Canonical status types (UI layers — not equal chips)

| Layer | Meaning | UI treatment | Authority |
|-------|---------|--------------|-----------|
| **Lifecycle (catalog)** | Build activ / inactiv in DB | One durable chip | Catalog / `db_active` |
| **Publication** | DRAFT…PUBLISHED / LEGACY_UNSPECIFIED | Distinct gate strip | Publication API |
| **Readiness / E2E** | STATIC_READY / BLOCKED / … | Progressive diagnostics | E2E readiness API |
| **System integration** | System Link Check hops | Table, not chips | Readiness findings |
| **Configuration** | Composition / contracts progress | Checklist / counts | Authoring panels |
| **Shell roadmap** | Planned section placeholder | Secondary nav meta only | Shell config |

**BUILD vs TEMPLATE:** Build = catalog/DB active axis. Template publication = separate axis. Never conflate.

---

## 2. Owner decisions (locked)

| Decision | Implementation choice |
|----------|----------------------|
| **Planificat** | **RENAME + MOVE + DEMOTE** — sections are **non-functional** → keep secondary label **„În dezvoltare”**; not product header; not lifecycle chip; not CTA |
| **Publică fail-closed** | Never enabled when readiness BLOCKED (or not publishable); disabled reason + primary blocker (Aluminiu human primary, code secondary); FE enforces honesty even if publication GET lies |
| **Visual** | Keep WorkOS dark shell; lighten PS content; max ~2 surface levels; fewer nested cards/badges |
| **Actions order** | Save draft → Validate → Check product path → Publish (visible disabled when blocked) |
| **Aluminiu** | Remains inactive / BLOCKED — no activation |

---

## 3. Action hierarchy

1. **Salvează** (draft / dossier save)
2. **Validează**
3. **Verifică** (E2E / product path)
4. **Publică** (always visible when action present; **disabled** when gate closed)

---

## 4. Route maps

| Route | Role |
|-------|------|
| `/product-system/products` | Only operational shell section |
| `/product-system/products/:code` | Template detail + authoring tabs |
| `/product-system/blueprint-dossier` | Dossier Studio + sticky actions |
| `/product-system/{components,…}` | Non-operational placeholders |

---

## 5. WorkOS tokens / patterns (prefer existing)

- Shell: `woSurfaces.app` `#0A0F1C` (unchanged)
- Content: prefer `surface` / `surfaceRaised` (`#111827` / `#1A2236`) over nested `#0B1220` / `#0D1321` stacks
- Borders: `woBorders.subtle` sparingly
- No independent PS palette

---

## 6. Figma

| Item | Value |
|------|-------|
| File | `0CDPIuqoaZ1OQgNnvNyl1F` |
| Page | PS — Authoring Studio `91:2` |
| Class | NEEDS_POLISH / DESIGN_ONLY — not FINAL without evidence |

---

## 7. Top-of-page inventory (target)

1. App chrome (unchanged)
2. PS shell title + Pricing Registry
3. Shell nav: **Products** primary; planned sections demoted secondary
4. Catalog (when on products)
5. Detail header: human name · lifecycle chip · publication gate · **primary blocker** · next action
6. Primary tabs → diagnostic secondary
7. Panel content (≤2 surface levels)

---

## 8. Components (allowlist touch)

- `productSystemShellConfig.ts`, `ProductSystemLayout.tsx`, `ProductSystemPlannedSectionPage.tsx`
- `TemplateDualStatusChips.tsx`, `ProductSystemTemplateDetailPanel.tsx`
- `ProductTemplatePublicationPanel.tsx`, publication gate helper
- `ProductE2EReadinessPanel.tsx` (clarity / surfaces)
- `BlueprintDossierStudio.tsx` sticky Publică honesty
- `vite.config.ts` + dev contract port alignment (proxy)
- Tests under `frontend/src/features/product-system/*`

---

## 9. APIs / fixtures / env

| Item | Truth |
|------|-------|
| Fixture | `TPL-VOLUMETRIC-LETTERS_v2` |
| Publication GET | May return `publish_allowed=true` with empty blockers when `last_e2e_verdict` null — **UI must not trust alone** |
| Readiness static | Authoritative for BLOCKED / Aluminiu |
| Proxy | Default FE must hit BE that serves `/publication` + `/e2e-readiness` (align to **8000** per AGENTS; stale **8001** process may 404) |
| READY fixture | Do **not** fake VL ready |

---

## 10. Forbidden paths

No: architecture reopen, business rule / schema / Product Truth / compilers / snapshots, Aluminiu activation, SVG/DWG/DXF, desktop transport, pricing, Execution materialization, mobile, CostEngine.

---

## 11. Checkpoint definitions

| CP | Meaning |
|----|---------|
| **CP0** | Shared map frozen (this doc) |
| **CP1** | Semantics + Planificat demotion + header hierarchy |
| **CP2** | Visual nesting / surface lighten |
| **CP3** | Fail-closed Publică + readiness clarity + proxy |
| **CP4** | Tests + screenshot matrix evidence |
| **CP5** | Worklog + final report + allowlist commits |

---

## 12. PASS / stop

**PASS** requires 10s comprehension, fail-closed Publică proof, Planificat not competing as product status, Aluminiu still BLOCKED.

**Stop** only if: BE rule change required for fail-closed; lifecycle ≠ architecture; proxy inseparable from dirty tree; Figma fundamental mismatch; new status needs schema; Aluminiu activation required; business rules must change.
