# Legacy & Dead Pieces — Cleanup Policy

**Version:** 1.0.0  
**Status:** Target architecture (documentation only)  
**Step:** 12 — NEEDS OWNER GO (no automatic deletion)

---

## 1. Rolul sistemului

Politica definește **cum tratăm** mock data, legacy components, demo pages, comp_flat_legacy, parent-only BOM, UI misleading, task catalogs paralele, unused templates, unused inventory links — **marchează, nu șterge automat**.

**Regulă:** **Nu șterge automat.** Clasifică → raportează → owner decide.

---

## 2. Ce detine

| Categorie | Conținut |
|-----------|----------|
| **Classification tags** | Standard taxonomy |
| **Inventory of dead pieces** | From audits |
| **Risk per piece** | Impact if removed vs kept |
| **Cleanup criteria** | When deletion allowed |
| **Migration notes** | If legacy still serves compat |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Automatic code deletion |
| Runtime deprecation switches (without GO) |
| Database cleanup scripts |
| Refactor execution |
| UI removal |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Full modular flow audit 2026-06-30 | tmp/FULL_MODULAR_PRODUCT_FLOW_AUDIT_REPORT_20260630.md |
| Master plan §9.8 | Step 12 list |
| Code reference checks | Zero-import before delete — future |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Tagged component list | Step 12 execution (future) |
| Owner decision queue | NEEDS_OWNER_DECISION items |
| UI legacy banners | Step 11 |
| Agent guardrails | Don't "fix" by deleting |

---

## 6. Source of truth — classification tags

| Tag | Meaning | Action |
|-----|---------|--------|
| `ACTIVE_OPERATIONAL` | Production use | Keep — maintain |
| `ACTIVE_READONLY_TRUTH` | Read-only canonical display | Keep — label |
| `ADMIN_REGISTRY` | Admin config | Keep — separate tabs |
| `ANALYTICS_ONLY` | Stats/post-job | Keep — label |
| `FUTURE_RESERVED` | Planned boundary | Keep — don't implement early |
| `LEGACY_COMPATIBILITY` | Old path still reachable | Mark — deprecate later |
| `MISLEADING_UI` | Shows wrong implication | Fix label first (Step 11) |
| `DEAD_PIECE` | Not connected to flow | Mark — owner decides delete |
| `HIGH_RISK_WRONG_DIRECTION` | Minute=price, cost-plus | Freeze — realign not extend |
| `NEEDS_OWNER_DECISION` | Unknown impact | Ask owner |

---

## 7. Conexiuni cu celelalte sisteme

Dead pieces **break** canonical flow when mistaken for truth:

```
DEAD: dossier-only components → skipped by CE on parent path
DEAD: comp_auto_1 UI synthesis → misleading ProductSystem truth
DEAD: V3 operation catalog → parallel task source
DEAD: Intake preview totals → mistaken for quote
DEAD: parent components_json=[] → blocks full orchestrator
DEAD: task_rules_json → docs only
DEAD: seed _ensure_v2_components when array empty

LEGACY: intake v3/v4/v5 routers
LEGACY: IntakeDetail path
LEGACY: comp_flat_legacy parsing
MOCK: DocumentCenter, ModuleChain demo events
```

Canonical flow must **not** depend on dead pieces — realignment Steps 7G–11 first.

---

## 8. Reguli owner obligatorii

1. **Nu șterge automat** — zero-import check + owner GO.
2. Step 12 **only after** 7G–11 — don't cleanup before alignment.
3. Mark MISLEADING_UI before DELETE.
4. Don't remove legacy until new path proven — **NEEDS_OWNER_DECISION** per piece.
5. Protected foundations (Intake V6, ProductDefinition, Aggregate, ExecutionActuals, HR) — **never** classified DEAD without explicit owner reversal.

---

## 9. Riscuri actuale din audit — catalog

| Piece | Tag | Risk if kept | Risk if removed |
|-------|-----|--------------|-----------------|
| Parent empty components_json | `DEAD_PIECE` | CE partial pricing | Break if something still reads parent only |
| Dossier costengine_mapping | `DEAD_PIECE` (for CE today) | Confusion | Lose audit reference |
| comp_auto_1 | `MISLEADING_UI` | Wrong component count | UI empty if removed without aggregate UI |
| V3 task catalog | `DEAD_PIECE` | Wrong task preview | Break preview until aligned |
| intakeV6OfferCalculator | `MISLEADING_UI` / preview | False official price | Remove operator visibility |
| intake v3/v4 routers | `LEGACY_COMPATIBILITY` | Parallel intake paths | Break old bookmarks |
| DocumentCenter mock | `DEAD_PIECE` / mock | Demo confusion | Low if unused |
| Markup as universal commercial | `HIGH_RISK_WRONG_DIRECTION` | Cost-plus | Break quotes until Step 8 |
| /price endpoint | `HIGH_RISK_WRONG_DIRECTION` + frozen | Mixed model | Break pricing until 7G–8 |
| Unused inventory materials | `DEAD_PIECE` | Accidental cost | Low if unreferenced |
| Duplicate lateral domain | `NEEDS_OWNER_DECISION` | Double counting risk | Break if wrong one removed |
| produce_order fallback | `HIGH_RISK_DEVIATED` | Wrong tasks | Break EP if removed without fix |

---

## 10. Target state (Step 12)

| Phase | Action |
|-------|--------|
| 1 | Classify all pieces (this doc + audit) |
| 2 | Step 11 labels on MISLEADING_UI |
| 3 | Canonical path works without dead pieces |
| 4 | Owner reviews DEAD list |
| 5 | Zero-import verification |
| 6 | Delete or archive with BUILD doc |

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Auto-delete after audit |
| Deprecate without classification |
| Remove /price before replacement (7G–8) |
| Delete dossier as "cleanup" without aggregate parity |
| Remove legacy intake without migration plan |
| Agent cleanup drive-by |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Full dead piece list | Audited items tagged |
| No silent DEAD in canonical path | Aggregate resolves |
| Owner queue | NEEDS_OWNER_DECISION enumerated |
| Step 12 gated | After 7G–11 GO |
| Zero-import policy | Documented for future deletes |

---

## Appendix — volumetric letters dead/mismatch summary

| Item | Status from audit |
|------|-------------------|
| Dossier 5 components | DEAD for CE on parent path |
| Parent 2 sablon materials only | Only priced parent lines today |
| Face/LED/cant/spate in breakdown | pricing-only ephemeral |
| Task preview ~13 ops | V3 catalog — not snapshot |
| can_generate_tasks: false | Dry-run honest if labeled |
| Quote 4 reprice | FROZEN — do not use as test fix |
