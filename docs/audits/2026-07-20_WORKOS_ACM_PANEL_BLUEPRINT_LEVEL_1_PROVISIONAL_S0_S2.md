# WORKOS_ACM_PANEL_BLUEPRINT_LEVEL_1_PROVISIONAL_S0_S2

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Mode | Implementation L1-P only — STOP owner review |
| Prerequisite audit | `WORKOS_ACM_PANEL_BLUEPRINT_LEVEL_1_READINESS_AUDIT` (approved) |
| Fixture | `IV6-DB2F86B7` / `a7b0162b-dc91-467f-aa24-c1279fb3a073` |
| Route | `/intake-v6/.../operator` · viewport 1440×900 |
| Evidence | `docs/audits/_evidence/2026-07-20_acm-panel-blueprint-l1-p/` |
| Worklog | `docs/worklog/realignment/2026-07-20_acm_panel_blueprint_level_1_provisional_s0_s2.md` |

---

## 1. Rezumat executiv

Build S0–S2 livrat: read model pur + schematic SVG read-only + slot sticky collapsed lângă inspector. Pe fixture canonic: **L1-P**, ansamblu **2000×350**, joint vertical derivat la x=1000, cote construction `catalog_default` ca provisional, litere fără overlay, banner composition inconsistency, disclaimer vizibil, **0 PUT** la interactiune blueprint. **Nu** se pretinde L1-C.

## 2. Verdict

**PASS** (L1-P provisional) — gates anti-fake-precision verificate.

## 3. HEAD / branch

| | |
|--|--|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `3ac9fb96a3ef8d486abfc21547d43063a560ff6e` |
| Feature commit | `c3267b563e01f10c4490dae02b3a3002a0430dd7` (`c3267b5`) |

## 4. Capability inventory

| Cap | Status |
|-----|--------|
| Repo/code search | USED |
| TypeScript | USED |
| Vitest | USED (26 + 35 regression) |
| Browser/Playwright | USED |
| Runtime API | USED `:8003` |
| SVG utilities | USED (host patterns; new mm schematic) |
| Screenshots | USED |
| Subagents | NOT USED |
| Figma | **NOT USED — NOT NEEDED** |
| 21st.dev | **NOT USED — NOT NEEDED** |

## 5. Figma / 21st status

```text
Figma: NOT USED — NOT NEEDED
21st.dev: NOT USED — NOT NEEDED
```

## 6. S0 read model

`frontend/src/lib/intakeV6/acmPanel/blueprintReadModel.ts` — `buildAcmPanelBlueprintReadModel`.

Contract: readiness, label, disclaimer, assembly, panels[], joints[], callouts[], constructionSection, relations[], missing/warnings/blockers, provenance, composition flags, collapsedSummary.

## 7. Readiness calculation

| Level | Când |
|-------|------|
| L0 | fără instance |
| L1-P | geometrie suficientă + orice câmp critic non-OC / segmented PROPOSED / composition inconsistent |
| L1-C | toate gate-urile (association+technical confirmed, segmented OK, critical OC, composition aligned) — **nu pe fixture** |
| L1-B | instance + geometrie panouri invalidă/contradictorie |

Fixture: **L1-P**.

## 8. Assembly dimensions

Multi-panel: extent panouri; `assembly_dimensions` dacă ±1 mm; **niciodată** envelope 1000. Expected/observed: **2000×350**.

## 9. Coordinate system

mm · origin top-left · +X right · +Y down. SVG bbox analysis **nefolosit** ca mm.

## 10. Panels

2 panouri 1000×350, order 1–2, authority proposed (segmented PROPOSED).

## 11. Joints

Linie verticală derivată x=1000; note „Rost schematic derivat”; **fără gap**.

## 12. Authority mapping

| Authority | Style / finality |
|-----------|------------------|
| operator_confirmed | solid_final / final |
| detected | solid_subtle / provisional |
| proposed | dashed_proposed / provisional |
| catalog_default | dashed_catalog / provisional |

## 13. Construction section

thickness/l1/l2/fold provisional catalog; rear/frame/mount omitted (inactive).

## 14. Relations

belongs_to_assembly show; positioned_on unknown → note only; mounts_on doar OC+operator.

## 15. S1 renderer

`IntakeV6AcmPanelBlueprintPreview.tsx` — SVG read-only, zero write props.

## 16. SVG structure

Assembly bounds + panel rects + order labels + joint line + overall callout.

## 17. Disclaimer

„Schematic Nivel 1 provizoriu — nu este desen de execuție.” + notă provisional pe L1-P.

## 18. Accessibility

`role="img"`, title/desc, aria-expanded toggle, contrast text, legendă nu doar culoare.

## 19. S2 placement

În `IntakeV6AcmPanelConfigRegion`: slot sticky collapsed lângă inspector (`xl` coloană 220–280px); formular prioritar.

## 20. Sticky behavior

`sticky top-2` pe preview; nu înlocuiește validation rail; grid list|inspector+preview|rail păstrat.

## 21. State honesty

Badge L1-P · Provizoriu; dashed catalog construction; proposed joint.

## 22. Composition inconsistency

Banner compact în preview expandat (fixture: product confirmed vs instance unconfirmed).

## 23. Negative fixtures

| Caz | Acoperire |
|-----|-----------|
| letters only → no slot | ConfigRegion.blueprint.test |
| no instance → L0 null | preview + read model tests |
| segmented PROPOSED → L1-P | read model + runtime |
| missing/invalid panels → L1-B | read model + preview |
| unknown positioned_on | read model + runtime |
| fold1+l2 warning | read model |
| composition inconsistent | runtime + tests |
| envelope ≠ assembly | read model warning |

## 24. Tests

- blueprintReadModel: **19** pass
- BlueprintPreview: **5** pass
- ConfigRegion.blueprint: **2** pass
- Regression AcmPanel: **35** pass

## 25. Runtime

`network-proof.json` **pass: true** — L1-P, 2000×350, joint 1000, refresh same.

## 26. Zero-write proof

Expand/collapse/hover/section/refresh → **0 PUT**.

## 27. Screenshots

| # | File | Expected | Observed | Verdict |
|---|------|----------|----------|---------|
| 1 | `01-configurare-full.png` | Configurare | captured | PASS |
| 2 | `02-inspector-collapsed-preview.png` | collapsed L1-P | 2000×350 · 2 panouri | PASS |
| 3 | `03-expanded-front.png` | schematic | SVG visible | PASS |
| 4 | `04-overall-2000x350.png` | overall label | 2000×350 | PASS |
| 5–6 | `05`/`06` | panels+joint+construction | present | PASS |
| 7 | `07-composition-inconsistency.png` | banner | present | PASS |
| 8 | `08-disclaimer-relations.png` | disclaimer + letter note | present | PASS |
| 9 | `09-scroll.png` | full scroll | captured | PASS |
| 10 | `10-after-refresh.png` | same schematic | L1-P 2000 | PASS |
| L1-B / letters-only | vitest | covered without inventing runtime WS | PASS |

## 28. Visual audit

Preview compact collapsed; expand nu domină formularul pe 1440; disclaimer clar; fără precizie falsă.

## 29. Regression

uiReadModel, operatorPatch, drafts, instantiate, inspector commitSemantics, component list — green. SvgAnalyzer neatins.

## 30. Boundaries

Fără DXF/export/PDF/CNC/unfold/nesting/BOM/pricing/tasks/totem/MULTI/DB/migrations/Fundal writes/PD owner changes.

## 31. Dead pieces

Nu am introdus path-uri dossier/PDF/production blueprint. Bond flat pattern neatins.

## 32. Risks

| Risc | Mitigare aplicată |
|------|-------------------|
| Fake precision | catalog/proposed dashed; final doar OC |
| Envelope 1000 as overall | extent/assembly_dimensions |
| Write ownership | zero write props + 0 PUT proof |
| Confused for execution drawing | disclaimer obligatoriu |

## 33. Roadmap

Owner accept → confirmări operator pe fixture → L1-C natural. Nu forța L1-C în UI.

## 34. Commit

| | |
|--|--|
| Full | `c3267b563e01f10c4490dae02b3a3002a0430dd7` |
| Short | `c3267b5` |
| Message | `feat(intake-v6): AcmPanel Blueprint L1-P provisional schematic` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Before | `3ac9fb9` |
| Files | 22 (+3123 / −8) |
| Tests | 26 blueprint + 35 regression Vitest; runtime `pass: true` |

## 35. Opinia sinceră

L1-P e util acum tocmai pentru că arată **2000** și nu minte că e confirmat. Cel mai important gate a fost envelope vs assembly — dacă trecea 1000, build-ul trebuia respins.

## 36. Cat suntem in directia stabilita: 88/100

Domain + projection + honesty + zero-write pe fixture. −12 pentru L1-C încă departe (intenționat) și lipsa dimension-line component reutilizabil mai general.
)
