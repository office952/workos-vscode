# Volumetric Intake Page Contract — TPL-VOLUMETRIC-LETTERS

**Date:** 2026-06-07  
**HEAD reference:** `942e1f0`  
**Scope:** Dedicated Work Intake shell for volumetric letters only

---

## 1. Purpose

`IntakeDetail` (`/intake/:id`) was a generic CRM wrapper mixing families, legacy fields, backend assist, totem terrain, CUI, and the real volumetric product form.

This contract defines a **dedicated route** (`VolumetricLettersIntakePage`) so operators working on `TPL-VOLUMETRIC-LETTERS` see a clean template workspace — not the full generic page.

**This is routing/shell cleanup, not a product editor rewrite.**

---

## 2. What belongs on the volumetric page

| Section | Content |
|---------|---------|
| **A. Context** | Intake code, client, contact, assigned_to, delivery_type, short description, status badge |
| **B. Action map** | Template / spec / terrain / intake status, primary next action, missing reasons |
| **C. Template** | Confirmed badge `TPL-VOLUMETRIC-LETTERS` OR compact confirm step (no full BackendAssist after confirm) |
| **D. Product spec** | `Product001IntakeSpecEditor` — all 11 sections, save, Vector Studio |
| **E. Handoff** | One clear **Deschide ofertare preliminară** → `VolumetricLettersQuoteFlow` |
| **F. Gate** | `ready_for_quote`, missing reasons, **Marchează Gata pt. Ofertă** (unchanged policy) |
| **G. Terrain** | Only when `delivery_type === delivery_install`; `isTotemFamily={false}` |

---

## 3. What does NOT belong (prominent)

- CUI / SmartBill / fiscal identification as primary workflow
- Live mode / mockData infrastructure banners
- Full `BackendAssistSection` after template confirmation
- Material/Sheet Assist, Sheet Quality links as primary panels
- Generic `product_family` + free-text `dimensions` as source of truth
- Totem fields: foundation, macara, surface type, totem height
- Duplicated bottom `NextStepPanel`
- Duplicate quote CTAs (editor prep panel disabled on volumetric shell; handoff section owns CTA)

These remain on the **generic** `IntakeDetail` path for other families.

---

## 4. Relations

| Artifact | Role |
|----------|------|
| `Product001IntakeSpecEditor` | **Core product form** — unchanged JSON contract |
| `VolumetricLettersQuoteFlow` | Quote workspace — unchanged; opened via `/quotes` nav state |
| `evaluateIntakeReadyPrerequisites` | Readiness policy — unchanged |
| `IntakeActionSummary` | Reused action map |
| `AuditTerenSection` | Install-only terrain; `isTotemFamily={false}` on volumetric route |

---

## 5. Routing rule

```text
shouldUseVolumetricIntakePage(confirmed_template_code, product_family)
  = confirmed === TPL-VOLUMETRIC-LETTERS
    OR (no confirmed AND family is litere_volumetrice)
```

`IntakeDetail` renders `VolumetricLettersIntakePage` when true; otherwise generic page.

---

## 6. Terrain visibility

| delivery_type | Terrain UI |
|---------------|------------|
| `courier`, `pickup`, `delivery_standard`, `delivery_express` | Compact **Teren: N/A (fără montaj)** — no blocking red section |
| `delivery_install` | Full install audit panel (non-totem) |

---

## 7. Readiness / status rule

- Use existing `evaluateIntakeReadyPrerequisites` — **no policy change**.
- If `status === ready_for_quote` but template/spec/readiness missing → show warning:

  > Statusul salvat pare mai avansat decât datele completate. Completează pașii lipsă înainte de ofertare.

- Do not auto-fix data in this build.

---

## 8. Non-goals

- No pricing / CostEngine changes
- No Reference Catalogs
- No `product_spec_json` contract change
- No `Product001IntakeSpecEditor` rewrite
- No quote/order creation in validation

---

## 9. Implementation map

| File | Responsibility |
|------|----------------|
| `lib/volumetricIntakeRoute.ts` | Route + status conflict helpers |
| `components/workos/VolumetricLettersIntakePage.tsx` | Dedicated shell |
| `pages/IntakeDetail.tsx` | Thin router; generic path unchanged |
