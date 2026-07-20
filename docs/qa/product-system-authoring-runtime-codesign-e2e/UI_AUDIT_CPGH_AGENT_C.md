# Full-page UI audit — Agent C (CP-G / CP-H)

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Verdict UI acceptance | **PARTIAL** |
| Stack | FE 3000/3011 up; BE 8000 has publication+readiness; BE 8011 lacks them; FE3000 API proxy → 404 |
| ProductSystem.tsx | **DIRTY — not edited** (foreign risk; catalog detail uses separate panel) |

## 1. Surfaces audited

### Product System catalog + template detail
- Dark WorkOS shell coherent; Romanian primary labels OK.
- Catalog honesty good: `Blocat (pregătire)`, `N blocaje`, Live DB badge, PLANIFICAT tabs not fake-complete.
- Detail **Prezentare** is strong narrative (Legea Modularității, axe de adevăr) but **Lifecycle** still hosts the older `TemplateLifecycleReadinessPanel` (`OWNER_GATE_REQUIRED`, score 100/100) — **not** the new publication lifecycle panel. Operators can confuse “lifecycle readiness” with “template publication”.
- New `ProductTemplatePublicationPanel` / `ProductE2EReadinessPanel` are **not mounted** on the catalog detail shell (`ProductSystemTemplateDetailPanel`). They appear on Blueprint Dossier Studio (+ older editor general tab path, which was not reachable via `open-editor` in this session).

### Blueprint Dossier Studio
- Sticky footer present and readable (`Deschide șablonul` / `Salvează dossier`).
- Authoring rail shows Publicare + Contracte + E2E Readiness — correct placement.
- Live failure: all three hit **HTTP 404** through FE proxy. Copy still states `active != published` and “publicarea este blocată de E2E Readiness” — good honesty in static text, but empty of real status badges until FE points at BE8000 (or 8011 is restarted with current code).

### Intake Confirmare (fixture IV6-DB2F86B7)
- Confirmare step reachable; matches Figma intent: blocked confirm, checkbox incomplete, sticky “Continuă către ofertă” disabled.
- Honest blockers: `runtime_capture_blocked`, composition/ACM inconsistency on Configurare, Confirmare incomplete 2/3.
- Visual density high but operator-readable; PinFooter pattern reused conceptually.

## 2. Figma

| Item | Result |
|------|--------|
| Intake refs 66:2, 64:2, 65:2, 65:106, 67:18 | All verified via `get_metadata` |
| PS Authoring Studio page | Created `91:2` with frames `91:3`, `91:12`, `91:21`, `91:36`, `91:60` |
| FINAL promotion | **Not done** — frames marked PROPOSED; UI acceptance cannot be PASS for Figma FINAL |

## 3. ENVIRONMENT_FAILURE (honest)

1. FE `3000` `/api/v1/product-system/*` → **404** while BE **8000** serves publication + readiness **200**.
2. BE **8011** openapi has **no** e2e-readiness/publication paths — stale process relative to branch HEAD.
3. Do **not** treat 404 panels as product FAIL of the React components; treat as stack wiring.

## 4. UI acceptance verdict

**PARTIAL**

Reasons (any one blocks PASS):
- PS Figma frames exist but are not owner-FINAL.
- Publication/readiness not on primary catalog detail surface.
- Live publication/readiness state load fails via FE proxy (ENVIRONMENT_FAILURE).
- Confirmare reachable and honest, but commercial freeze screenshot pack incomplete by design of environment.

Not **FAIL**: no fake PASS, no invented Figma IDs, no aluminiu activation, dirty tree preserved, App.tsx untouched.

## 5. PAREREA MEA SINCERĂ (UI)

UI-ul de catalog e matur ca limbaj (română, badge-uri oneste, dark shell), dar **coloana vertebrală nouă de publicare stă ascunsă în Dossier** în timp ce tab-ul Lifecycle din catalog încă vinde alt model (`OWNER_GATE_REQUIRED` / score). Asta e cea mai mare minciună blândă a ecranului: arată “gata 100/100” lângă “4 blocaje” fără să arate `publication_status` și `active ≠ published`. Până FE lovește BE-ul care chiar are API-urile și până panourile noi stau pe detail-ul pe care operatorul îl deschide zilnic, verdictul rămâne PARTIAL — corect, nu rușinos. Figma Intake e autoritate solidă; frame-urile PS pe care le-am creat sunt schelet util, nu FINAL. Nu aș declara PASS UI doar ca să închid gate-ul.
