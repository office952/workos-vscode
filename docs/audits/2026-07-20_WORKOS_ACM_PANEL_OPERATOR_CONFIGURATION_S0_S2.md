# WORKOS_ACM_PANEL_OPERATOR_CONFIGURATION_S0_S2

**Status:** Implementation complete — STOP owner review  
**Date:** 2026-07-20  
**Workspace proof:** `IV6-DB2F86B7`  
**Evidence:** [`docs/audits/_evidence/2026-07-20_acm-panel-operator-s0-s2/`](./_evidence/2026-07-20_acm-panel-operator-s0-s2/)  
**Worklog:** [`docs/worklog/realignment/2026-07-20_workos_acm_panel_operator_configuration_s0_s2.md`](../worklog/realignment/2026-07-20_workos_acm_panel_operator_configuration_s0_s2.md)

---

## 1. Rezumat executiv

Build unic S0–S2: read model AcmPanel, listă sibling de componente, inspector cu progressive disclosure, validation rail, single `operatorPatch`, Fundal ACP read-only când există instanță. SvgAnalyzer freeze respectat. Composition nu se auto-confirmă; honesty UI arată **Inconsistență stare** când product composition e confirmed dar instanța e unconfirmed.

## 2. Verdict

**PASS condiționat owner** pe dovezi locale (teste + runtime + screenshots). Nu e „greenwash”: pe fixture există încă blockers (segmentare PROPOSED, association proposed) — corect, nu ascunse.

## 3. HEAD / branch

| | |
|--|--|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `7c72250271471dba88ff753543cb9096b8b797c1` |
| Commit | (vezi §38) |

## 4. Capability usage

Vitest, pytest coalesce, Playwright 1440×900, API `:8003`, audit evidence 21st/Figma (fără nouă cercetare). TypeScript full gate **not claimed**.

## 5. Workstreams

S0 read model → S1 list/inspector → S2 patch+Fundal RO → Review mount → tests/runtime/docs/commit.

## 6. Large-file boundaries respected

| Boundary | Respectat |
|----------|-----------|
| OW shell thin | da — neatins |
| Review mount only | da — +~59 LOC wiring |
| SvgAnalyzer freeze | da — zero diff |
| Extrageri obligatorii | da |
| Fundal not second write | da când instance exists |
| No prep refactor | da |

## 7. S0 uiReadModel

`frontend/src/lib/intakeV6/acmPanel/{resolveInstance,uiReadModel}.ts` — singurul translator; coalesce top→selection→mounting; labels operator; issues cu section/field targets.

## 8. S0 Composition truth

`IntakeV6ProductCompositionPanel` consumă `compositionHonesty`. Badge: Compoziție propusă / Inconsistență stare / Confirmată de operator. Runtime proof: badge **Inconsistență stare** pe IV6-DB2F86B7.

## 9. S0 Field authority

`Propunere din catalog` / Detectat / Propus / Confirmat de operator via `authorityHintForField`. Catalog ≠ confirmed.

## 10. S1 Component list

`IntakeV6ProductComponentList` — Litere / Logo / Panou Alucobond; segmente nu sunt sibling.

## 11. S1 Selection

`useIntakeV6ProductComponentSelection` — sessionStorage per workspace; nu scrie payload.

## 12. S1 Inspector shell

`IntakeV6AcmPanelInspector` + `IntakeV6AcmPanelConfigRegion` layout list | inspector | rail.

## 13–19. S2 sections

Rezumat, Geometrie, Construcție (confirm construction / technical), Segmente (reuse SegmentedBackgroundPanel), Material (read), Structură/montaj, Relatii (geo vs mounts), Detalii tehnice collapsed.

## 20. Technical confirmation

`buildAcmPanelConfirmTechnicalPatch` — setează authorities + technical/association confirmed; **nu** composition.

## 21. Composition confirmation

CTA existent; explicit; no auto.

## 22. Validation rail

`IntakeV6AcmPanelValidationRail` — Blocante/Avertizări/Observații; click → select acm + open section + scroll/focus.

## 23. Preview

Existând sticky comercial; fără blueprint. Highlight segment: via existing segmented UI only.

## 24. Legacy Fundal

`IntakeV6AcmPanelFundalSummary` când instance exists; inputs ACP editabile doar dacă **nu** există instanță (legacy orphan path).

## 25. Single write-path

`operatorPatch.ts` → Review `persistFinishSetupState` immediate; sync top-level + embeds.

## 26. Tests

| Suite | Result |
|-------|--------|
| uiReadModel.test | 7 pass |
| operatorPatch.test | 4 pass |
| instantiate.test | 3 pass |
| ProductCompositionPanel.test | 5 pass |
| ProductComponentList.test | 1 pass |
| pytest coalesce | 3 pass |

## 27. Runtime proof

`IV6-DB2F86B7`: după confirm construction — top-level instance present; `fold_count` → `operator_confirmed`; `composition_status` still `unconfirmed`; composition honesty inconsistency visible.

## 28. Screenshots

Dir: `_evidence/2026-07-20_acm-panel-operator-s0-s2/` @1440×900

| File | Expected | Observed | Verdict |
|------|----------|----------|---------|
| 01–03 | Config/list | shell + list region | OK |
| 04 | Litere selected | row select | OK |
| 05–06 | Acm selected + summary | Blocat + axes | OK |
| 07–09 | geometry/construction | sections + confirm | OK |
| 10–11 | segments/relations | nested | OK |
| 12 | validation rail | blockers | OK |
| 13 | Fundal RO | capture landed pe inspector/segments (Montaj scroll) — Fundal code path exists | PARTIAL visual |
| 14 | composition honesty | Inconsistență stare | OK |
| 17–19 | refresh / Straturi | reopen | OK |

## 29. Visual audit

WorkOS density păstrată; list+inspector+rail citesc ca Configurare, nu SaaS dashboard. Badge noise pe rail e util (critical fields). Footer warnings rămân. Opinie: ierarhia e corectă; Fundal Montaj merită scroll-to-summary în follow-up.

## 30. Payload

Operator patch upsert scrie `acm_panel_instance` top-level + mounting/selection embeds.

## 31–32. PD / Aggregate

Nu s-a schimbat contractul; top-level promote îmbunătățește PD coalesce. Fără pricing/task side effects din proposal.

## 33. Pricing/task boundaries

Respectate — segmented copy încă spune no pricing/tasks; composition confirm separat.

## 34. LOC/effect metrics

ReviewStep: 3757→3816 lines; useEffect 24→24. New logic outside Review.

## 35. Dead pieces

Orphan SupportContourGeometryCard neatins. Editable Fundal path rămâne doar fără instanță.

## 36. Risks

| Risc | Mitigare / residual |
|------|---------------------|
| Review încă mare | +59 LOC only |
| Composition inconsistency pe fixture vechi | honesty UI — operator must re-confirm composition after technical |
| Screenshot 13 Fundal RO partial | code present; visual follow-up |
| Confirm construction ≠ association confirmed | intentional until Confirmă configurația tehnică |

## 37. Roadmap

1. Owner GO accept  
2. Optional: scroll-to Fundal summary on Montaj tab  
3. Later: association confirm UX explicit; clear-path parity  
4. Later: Review decomposition (not this build)

## 38. Commit

| | |
|--|--|
| Full | `4f9717b68b4868459dfbc5e2873c151c9e84de31` |
| Short | `4f9717b` |
| Message | `feat(intake-v6): AcmPanel operator configuration S0-S2` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Before | `7c72250271471dba88ff753543cb9096b8b797c1` |
| After | `4f9717b68b4868459dfbc5e2873c151c9e84de31` |

## 39. Opinia sinceră

Build-ul face treaba grea: adevărul nu mai minte cu „Confirmat”, panoul e sibling, Fundal nu mai e al doilea editor. Review încă e un monstru, dar n-am turnat inspectorul în el. Fixture-ul arată intentional „Blocat” — asta e corect, nu e eșec UI. Următorul pas e operator hygiene (confirm segmentare + composition re-sync), nu redesign.

## 40. Cat suntem in directia stabilita: **78/100**

Domain+UI presentation alignment up sharply from audit 57; residual blockers pe fixture + Fundal screenshot partial țin scorul sub 85.

---

## 21st / Figma mapping (from approved audit)

| Implementare | 21st | Figma | Adaptat | Respins |
|--------------|------|-------|---------|---------|
| Component list | settings 2618 / sidebar 19371 | Finisaje `23:3` | densitate WorkOS | glass SaaS |
| Status chips | card-status 2514 | status tokens | vocab RO | motion spam |
| Accordion sections | accordion 506 | Litere `47:145` | one-level | deep nest 8041 |
| Validation rail | toolbar ideas | footer CTA | sticky compact | floating pills |
| Segment nested | table-edit 7457 | — | reuse Segmented panel | new editor |

---

## STOP — Owner gate

Implementare livrată. Așteaptă review owner. Fără remediation / blueprint / MULTI.
