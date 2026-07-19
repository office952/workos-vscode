# Intake V6 — Letter Pilot Completion Design Checkpoint

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `8aafbd1b05c522d6f22b2f9acd737e83809e43dd`  
**HEAD at checkpoint:** `7a3bf6f383ac4a18abb5226101cb4b9f48b50067` (docs hash note on baseline)  
**Stack:** FE `:3000` · `BACKEND_PORT=8003` · BE `:8003` (proxy verified same workspace)  
**Mode:** Checkpoint before implementation — frontend presentation only

---

## Pre-flight snapshot

| Item | Value |
|------|--------|
| Foreign WIP | Present (availability, shell screenshots, segmented runtime, etc.) — untouched |
| FE / BE | 200 / healthy |
| Proxy | `:3000/api` → `:8003` confirmed |
| Active composition | `IntakeV6ProductCompositionPanel` |
| Active scope | `IntakeV6OfferScopeReviewSummary` + blocker banner |
| Pricing rail | `IntakeV6LiveCalculationSummary` (`rightPanel`/`bar`) + `IntakeV6PricingInputPanel` |
| Viewport | `lg` two-column; rail sticky `top-4`; mobile price bar |
| Letter pilot | `v6Pilot` on Finisaje letter groups + Iluminare decisions/results |
| L1 technical still visible | Composition item mono codes behind `<details>`; scope always-on violet card; pricing lines always on desktop rail; commercial sliders always below rail |

---

## 1. Current full Page 2 hierarchy

1. Composition panel (full width, cyan/emerald card)  
2. Logo-only guard (conditional)  
3. Mobile price spine (`lg:hidden`)  
4. Grid left: Offer scope strip → Blocker/guidance banner → Tab nav → Finisaje/Iluminare/Montaj panels → save footer  
5. Grid right sticky: Live calc (totals + line preview) + commercial sliders  
6. Page diagnostic accordion (below grid)

---

## 2. Current letter pilot strengths

- Față/Cant/Spate anatomy zones with clearer typography (`v6Pilot`)  
- Iluminare: decisions vs `Rezultate calculate` split  
- Artwork metadata already demoted into technical accordion  
- Guidance spine (footer / sticky counts / drawer) intact  

---

## 3. Remaining visual competition

- Composition + violet scope cards equal-weight with product decisions  
- Sticky pricing rail wide (360–460px) with always-visible line rows + sliders  
- Multiple amber/cyan/violet banners before tabs  
- Technical composition/PD details still compete when panel is open  

---

## 4. Composition content classification

| Content | Class | Treatment |
|---------|-------|-----------|
| Product identity / composition type | Operator | Always visible compact |
| Major components (letters, support, logo) | Operator | Compact summary line |
| Confirmation status | Operator | Badge always visible |
| Confirmă CTA | Required decision | Always visible when actionable (not buried only in expand) |
| Blockers / warnings | Blocker/warning | Visible when present |
| Template codes / layer IDs / PD readiness | Technical | Disclosure only |
| Linked PD segments | Technical | Existing accordion |

---

## 5. Scope content classification

| Content | Class | Treatment |
|---------|-------|-----------|
| Mode (full / subset) | Informational / decision context | Compact one-liner |
| Active components | Informational | Compact |
| Excluded components | Informational | Disclosure |
| Blockers | Via operator blocker banner | Keep sticky banner |

---

## 6. Pricing rail classification

| Content | Class | Treatment |
|---------|-------|-----------|
| Gross/net / unavailable | Commercial result | Always visible |
| Pricing blockers / missing rates | Blocker/warning | Always visible |
| Line items / filters / logical list | Secondary detail | Collapsed by default |
| Commercial sliders | Secondary adjustment | Disclosure “Ajustări comerciale” |
| Calculations | Forbidden to change | Preserve all math/API |

---

## 7. Proposed primary / secondary / technical hierarchy

**Primary:** product identity → Finisaje Față/Cant/Spate → Iluminare decisions  
**Secondary:** calculated lighting results → commercial result (compact)  
**Tertiary:** composition/scope technical, pricing line detail, page diagnostics  

---

## 8. What moves behind disclosure

- Composition template codes / layer IDs / PD segments (already mostly)  
- Scope excluded list + verbose copy  
- Pricing line rows, filters, technical toggle (desktop default collapsed)  
- Commercial sliders panel  

---

## 9. What remains always visible

- Composition identity + status + confirm CTA when needed  
- Real blockers (composition issues + operator blocker banner)  
- Commercial total / unavailable + price blockers  
- Letter anatomy + lighting decisions  
- Footer primary action / sticky counts  

---

## 10. Responsive behavior

- `lg+`: quieter sticky rail, details on demand  
- `<lg`: compact price bar keeps totals; details via existing sheet  
- Confirm CTA and blockers must not hide behind collapse on narrow viewports  

---

## 11. Screenshot plan

Before/after: full Finisaje, composition, pricing compact/expanded, Iluminare, narrow, Confirmare, Montaj regression.

---

## 12. Regression plan

- No Montaj file edits  
- No analyzer/backend/domain  
- Support-role repair untouched  
- Confirmare access logic untouched  
- Pricing API payloads unchanged  
- Sticky/footer counts still driven by existing overlay  

**Implementation may begin after this checkpoint exists in the working tree.**
