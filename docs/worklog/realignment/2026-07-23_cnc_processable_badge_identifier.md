# CNC processable badge — capability identifier

**Date:** 2026-07-23  
**Status:** Documented + wired (Letters face + Utilaje CNC)

## Meaning

`CNC` chip is **not decoration**. It is the operator mark for:

**`BADGE-CNC-PROCESSABLE`**

= material can be processed on CNC **and** CNC utilaj carries the same badge.

## Contract

| Field | Value |
|-------|--------|
| Label (UI) | `CNC` |
| Stable code | `BADGE-CNC-PROCESSABLE` |
| Title RO | Procesabil CNC |

### Carriers (v1 — narrow)

| Kind | Codes / keys |
|------|----------------|
| Material (Letters face) | `MAT-ACP-FATA-LITERE` → display `plexiglas 3mm PMMA - opal` |
| Machine (only) | `MCH-CNC-4020` / display **CNC 4020** |

**Not carriers:** generic `cnc_router` type, shared `WC_CNC_ROUTING`, polystyrene CNC, CNC laser, other routers.

Letter-face services under the badge: Debitare · Șanfren / Canal.

## Implementation

| Layer | Path |
|-------|------|
| Frontend contract | `frontend/src/lib/cnc/cncProcessableBadge.ts` |
| Shared chip | `frontend/src/components/workos/CncProcessableBadge.tsx` |
| Backend mirror | `backend/services/cnc_processable_badge.py` |
| Letters structure | Product System V2 face row + process strip |
| Utilaje | list + detail for CNC 4020 only |
| Pricing Registry | `/inventory/pricing` row for `MAT-ACP-FATA-LITERE` only |
| Inventory | `/inventory` table (+ detail) for `MAT-ACP-FATA-LITERE` only |

## Out of scope (this pass)

- Inventory admin table column wiring (follow-up)
- Pricing Registry visual chip column
- Expanding badge to Forex / ACM without owner GO
