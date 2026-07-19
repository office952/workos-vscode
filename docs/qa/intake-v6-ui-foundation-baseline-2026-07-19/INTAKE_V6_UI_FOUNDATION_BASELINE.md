# INTAKE V6 UI FOUNDATION BASELINE

**Status:** FROZEN CHECKPOINT  
**Date:** 2026-07-19  
**Accepted HEAD:** `b1ba2ff`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Mode:** Consolidate — do not redesign structure

---

## Owner acceptance

| Surface | State |
|---------|--------|
| Page 1 (Straturi) | Closed |
| Composition summary | Closed |
| Finisaje ownership (`SURFACE_FINISH`) | Closed |
| Montaj IA | Closed |
| Segmented ACM/ACP + 220V | Closed functionally |
| Critical blockers | None |
| Direction | **99/100%** |

**Rule:** Montaj reopens only for a real operational risk.

**Rule:** Do not add features. Next changes must reduce noise.

---

## Frozen information architecture

```
Page 1 — Straturi
   ↓ analiza + confirmare roluri
Page 2 — Configurare
   ├── Finisaje
   │     ├── controale operator (Față · Cant · Spate · material/culoare)
   │     └── detalii tehnice (ownership / tokenuri)
   ├── Iluminare și surse
   │     └── LED / PSU truth
   └── Montaj
         ├── Fundal și carcasă
         ├── Segmentare
         ├── 220V
         ├── Comercial
         └── Avansat
   ↓
Confirmare
```

**Do not move this structure.**

---

## Accepted presentation pattern

```
1. Ce aleg acum?        → primary controls
2. Este complet?        → status / warnings
3. Detalii tehnice      → ownership / tokens / diagnostic
```

Technical truth may exist; it must not occupy the first visual level unless it requires action.

---

## Commits that established this baseline

| Commit | Subject |
|--------|---------|
| `fc9c21b` | Page 2 IA / Montaj realignment |
| `bfddb1e` | Operator vocabulary + mounting noise cleanup |
| `51ea07a` | Page 1 + composition clarity |
| `b1ba2ff` | Finisaje SURFACE_FINISH ownership demotion |

Supporting audits (read-only):

- `docs/qa/intake-v6-ui-consistency-audit-2026-07-19/INTAKE_V6_UI_CONSISTENCY_AUDIT.md`
- This baseline + display-label pre-GO inventory (sibling file)

---

## Explicitly out of bounds until new GO

- Analyzer / SVG processing changes
- ProductDefinition / ProductAggregate / binding contracts
- Pricing / CPP / Quote / Order / Execution
- Montaj IA changes
- Segmented / electrical logic changes
- Visual polish before meaning is closed
- Backend / schema / seeds / Employee Mobile

---

## Next build (waiting for GO)

**Name:** Finisaje + Confirmare Display Label Normalization  
**Type:** presentation truth only  
**Not:** redesign, analyzer change, Montaj reopen  

Pre-GO inventory:  
`DISPLAY_LABEL_NORMALIZATION_PRE_GO_INVENTORY.md`

Until GO: **no implementation.**
