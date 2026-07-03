# Prices V2 — Backend Readiness

**Generated**: 2026-06-03  
**Status**: ✅ LIVE — Materials and markup are fully wired

---

## Current State

### Fully Operational ✅

| Feature | API Client | Endpoint | Status |
|---------|-----------|----------|--------|
| Material list | `inventoryMaterialsAdmin.ts` | `GET /api/admin/inventory-materials` | ✅ Live |
| Material detail | `inventoryMaterialsAdmin.ts` | `GET /api/admin/inventory-materials/{code}` | ✅ Live |
| Price history | `inventoryMaterialsAdmin.ts` | `GET /api/admin/inventory-materials/{code}/price-history` | ✅ Live |
| Material update | `inventoryMaterialsAdmin.ts` | `PATCH /api/admin/inventory-materials/{code}` | ✅ Live |
| Markup config | `commercialMarkupPoliciesAdmin.ts` | `GET /api/admin/commercial-markup-policies/config` | ✅ Live |
| Markup policies list | `commercialMarkupPoliciesAdmin.ts` | `GET /api/admin/commercial-markup-policies` | ✅ Live |
| Markup dry-run | `commercialMarkupPoliciesAdmin.ts` | `POST /api/admin/commercial-markup-policies/dry-run` | ✅ Live |
| ProductSystem pricing | `productSystemPricingPreviewAdmin.ts` | `POST /api/admin/productsystem-pricing-preview` | ✅ Live |
| Source review audit | `inventoryMaterialsAdmin.ts` | `GET /api/admin/inventory-materials/{code}/source-review-audit` | ✅ Live |

---

## Actions That Can Be Connected Real

| Action | Endpoint | Current UI State | Wiring Needed |
|--------|----------|-----------------|---------------|
| View material details | `GET /api/admin/inventory-materials/{code}` | ✅ Connected | None |
| View price history | `GET /api/admin/inventory-materials/{code}/price-history` | ✅ Connected | None |
| Edit material cost | `PATCH /api/admin/inventory-materials/{code}` | ⚠️ Button disabled | Wire form → PATCH |
| Refresh material list | `GET /api/admin/inventory-materials` | ✅ Connected | None |
| Run dry-run simulation | `POST /api/admin/commercial-markup-policies/dry-run` | ✅ Connected | None |
| View markup policies | `GET /api/admin/commercial-markup-policies` | ✅ Connected | None |

---

## Actions Currently Disabled (with reasons)

| Action | Disabled Reason | Endpoint Needed |
|--------|----------------|-----------------|
| Edit cost (inline) | "Necesită endpoint" — actually exists! | `PATCH /api/admin/inventory-materials/{code}` |
| Edit markup (inline) | "Necesită endpoint" | `PUT /api/admin/commercial-markup-policies/{id}` (may not exist) |
| Create new material | Not in current UI | `POST /api/admin/inventory-materials` (may not exist) |
| Delete material | Not in current UI | `DELETE /api/admin/inventory-materials/{code}` (may not exist) |
| Create markup policy | Not in current UI | `POST /api/admin/commercial-markup-policies` (may not exist) |

---

## P1 Quick Wins

### 1. Enable "Edit cost" button

The `PATCH /api/admin/inventory-materials/{code}` endpoint **already exists**. The button is disabled with tooltip "Editare cost — Necesită endpoint" but the endpoint is available.

**Work needed**: 
- Add inline edit form or modal
- Call `PATCH /api/admin/inventory-materials/{code}` with `{ unit_cost: newValue }`
- Refresh material list after successful update
- Show success/error toast

### 2. Enable "History" view

The `GET /api/admin/inventory-materials/{code}/price-history` endpoint **already exists** and is already connected in the API client.

**Work needed**:
- Verify the history panel is rendering data from the API (may already work)
- Ensure proper date formatting and change reason display

---

## Boundary Rules

- ❌ No TVA (VAT) display or calculation in Prices V2
- ❌ No "total cu TVA" column
- ❌ No "include TVA" toggle
- ❌ No modification to CostEngine logic
- ❌ No modification to Commercial Markup calculation logic
- ✅ `unit_cost` = acquisition/production cost only, NOT commercial price
- ✅ Source metadata = verification reference, not price truth
- ✅ Markup is applied by backend dry-run, not computed in UI

---

## Data Flow

```
Material Registry (GET /api/admin/inventory-materials)
  → unit_cost (acquisition cost)
  → source metadata (supplier, URL, review status)
  
Commercial Markup (GET /api/admin/commercial-markup-policies)
  → scope (global/category/material)
  → markup_type (percent/fixed/hybrid)
  → priority + conflict resolution
  
Dry-Run (POST /api/admin/commercial-markup-policies/dry-run)
  → material_code + quantity
  → returns: base_cost + applied_policy + markup_amount + commercial_price
  
ProductSystem Preview (POST /api/admin/productsystem-pricing-preview)
  → product template + quantities
  → returns: component costs + total production cost + markup
```

---

## Summary

Prices V2 is the **most operationally ready** module in the system. All read operations are live, dry-run simulation works, and the only gap is wiring the "Edit cost" button to an endpoint that already exists. This is a ~1 hour fix.