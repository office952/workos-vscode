# Standard confirmation checklist — Intake V4 analyzer builds

Any build that touches one or more of these areas must complete this checklist before declaring **PASS**:

- SVG Analyzer
- layer roles
- pseudo-layers
- artwork classification
- raster/image handling
- geometry quote
- material breakdown
- Oracal / vinyl finish pricing
- edge/cant rules
- CNC/LED preview
- Intake V4 operator UI

**No PASS verdict without a complete checklist** (or explicit **PASS scoped** / **HOLD push** with gaps listed).

Related automation:

- `frontend/src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts`
- `frontend/e2e/intake-v4-analyzer-regression-gate-smoke.spec.ts`
- `docs/architecture/SVG_ANALYZER_REGRESSION_GATE_POLICY.md`

---

## 1. Git / branch confirmations

Report obligatoriu:

1. Branch curent.
2. HEAD before.
3. HEAD after.
4. Remote HEAD before.
5. Remote HEAD after (dacă s-a făcut push).
6. Commituri ahead față de remote.
7. Git status final.
8. Confirmare tracked clean.
9. Confirmare untracked necomise: `docs/audit/`, `tmp/`, `test-results/`, QA docs unrelated.
10. Confirmare fără rebase.
11. Confirmare fără merge.
12. Confirmare fără force push.
13. Confirmare fără commit nou necerut.

---

## 2. Fixture coverage obligatoriu

Pentru schimbări în analyzer / SVG / layer roles, rulează sau raportează explicit:

1. **PBL:** `pbl-layere.svg`
2. **Ana Maria layered:** `ana-maria-gradinita.svg`
3. **Ana Maria unlayered:** `ana-maria-gradinita-fara-layere.svg`

Dacă unul nu este rulat, verdictul nu poate fi **PASS** complet. Maxim **PASS scoped** / **HOLD push**.

---

## 3. PBL baseline confirmations

Pentru `pbl-layere.svg`, confirmă:

1. Width ≈ 2700 mm.
2. Height ≈ 350 mm.
3. Layer structure păstrată dacă era validă.
4. Nu se aplică pseudo-layer agresiv peste structura validă.
5. Real letters / child parts = 10.
6. Child parts total = 11 (10 letters + 1 artwork/emblem conform baseline).
7. Face area ≈ 0.691 m².
8. LED exterior perimeter ≈ 11.63 m.
9. CNC face perimeter ≈ 13.62 m.
10. Holes/interiors = 5.
11. Cut contours = 15.
12. Layer principal coerent.
13. Confirm all auto roles funcționează.
14. Confirmation status nu rămâne `missing` dacă rolurile sunt confirmabile.
15. Raster/image nu devine child part.
16. Artwork rămâne artwork.
17. Material Breakdown nu pierde rânduri.
18. CNC operation rows rămân corecte.
19. LED modules / W / PSU rămân corecte dacă se atinge zona.
20. Edge/cant metrics rămân corecte dacă se atinge zona.

---

## 4. Ana Maria layered confirmations

Pentru `ana-maria-gradinita.svg`, confirmă:

1. 6 entități/layers detectate.
2. `gradinita` = Față litere / geometrie volumetrică.
3. `ana` = Față litere / geometrie volumetrică.
4. `maria` = Față litere / geometrie volumetrică.
5. `soare` = Față litere / geometrie volumetrică.
6. logo stânga = Artwork / print / autocolant.
7. logo dreapta = Artwork / print / autocolant.
8. Cele 4 culori solide recunoscute: portocaliu, verde, albastru, roșu.
9. Logo-uri/rastere nu devin child parts.
10. Raster-over-vector: raster = artwork, vector = production geometry.
11. Artwork complexity recomandă print + laminare dacă există raster/multe culori.
12. Confirm all → `complete`.
13. Confirmation nu rămâne `missing`.
14. Geometry quote nu arată fals `—` fără explicație.
15. Dacă split pe litere individuale nu e posibil: mesaj production geometry detected, child split pending/manual.

---

## 5. Ana Maria unlayered confirmations

Pentru `ana-maria-gradinita-fara-layere.svg`, confirmă:

1. Nu rămâne un singur `Layer_x0020_1` în UI.
2. 6 pseudo/raster entități generate.
3. 4 pseudo-layere vectoriale solide = Față litere / geometrie volumetrică.
4. 2 raster/logo = Artwork / print / autocolant.
5. Culori solide grupate separat (orange/gradinita, green/ana, blue/maria, red/soare).
6. Rastere separate stânga/dreapta.
7. Rastere nu devin child parts.
8. Confirm all → `complete`.
9. Confirmation nu rămâne `missing`.
10. Geometry quote detectează production geometry sau afișează pending split/manual clar.
11. Artwork complexity recomandă print + laminare când e cazul.

---

## 6. Raster / artwork rule confirmations

Pentru orice SVG cu `<image>` / raster:

1. `<image>` detectat.
2. External image href detectat.
3. Missing external asset warning dacă asset lipsește.
4. clipPath/mask detectat dacă există.
5. Raster overlap cu vector detectat.
6. Raster = `face_artwork` / `print_overlay` / `printed_artwork`.
7. Vector suprapus rămâne `production_geometry`.
8. Rasterul nu generează: child part, CNC, cant/volum, LED perimeter, plexiglas face.
9. Aria print estimată din vector acoperit (MVP), nu bbox brut al imaginii.
10. Warning dacă aria este estimată.

---

## 7. Artwork complexity / print + laminare confirmations

1. >3 culori dominante → `print_on_vinyl_laminated`.
2. Raster/foto → `print_on_vinyl_laminated`.
3. Gradient → `print_on_vinyl_laminated`.
4. clipPath/mask complex → `print_on_vinyl_laminated`.
5. 1–3 culori plate → vinyl_cut sau manual review, nu print obligatoriu.
6. Operator UI afișează recomandarea.
7. Operator UI afișează motivul.
8. Operator poate accepta recomandarea.
9. Operator poate override manual dacă flow permite.
10. Decizia operatorului se persistă dacă implementat.
11. Material Breakdown: print vinyl + laminare preview/missing_rate dacă nu există prețuri.
12. Nu se creează taskuri reale.
13. Nu se consumă stoc.

---

## 8. Layer finish / Oracal pricing confirmations

Pentru builduri care ating finisaje / layers / material breakdown:

1. Fără finisaj = baseline.
2. 641 pe un layer → cost 641 corect.
3. 651 pe un layer → cost 651 corect.
4. 8500 pe un layer → cost 8500 corect.
5. 8500 pe două layere → cantitate/cost crește.
6. 651 + 8500 pe layere diferite → rânduri separate.
7. Scoaterea unui layer finisat scade costul.
8. Schimbare 8500 → 651 mută cantitatea corect.
9. Două layere aceeași serie se adună, nu se suprascriu.
10. Layere serii diferite rămân separate.
11. 641 nu este tratat ca 651.
12. 8500 nu este tratat ca 651.
13. Prețuri păstrate: 641 = 6.5 EUR/m²; 651 = 9 EUR/m² owner; 8500 = 20 EUR/m².
14. Pricing Registry nu suprascrie owner Oracal când `price_source` este owner/composite.
15. Non-owner registry override încă funcționează.

**Automated gate:** `backend/tests/test_intake_v4_layer_finish_pricing_matrix.py`, `test_intake_v4_oracal_641_651_pricing.py`

---

## 9. Edge / cant confirmations

1. Cant calculat corect.
2. Cant pentru preț cu waste corect.
3. Adeziv cant în ml.
4. Operații cant în m, nu ml.
5. Oracal 651 cant este m².
6. 1 layer `oracal_wrapped` produce cost.
7. 2 layers `oracal_wrapped` cresc costul.
8. 3 layers `oracal_wrapped` cresc costul.
9. Cant wrapped folosește 651, nu 641/8500.
10. Raster/artwork nu generează cant.
11. Edge/cant task source = `shared_edge_cant_rules`.
12. `consumes_stock_now=false` în preview.
13. `creates_task_now=false` în preview.

---

## 10. CNC confirmations

Dacă se atinge geometry / face / backing / operation rows:

1. CNC face cut corect.
2. CNC face bevel corect.
3. Backing cut doar dacă backing activ.
4. Forex 10 mm backing cut = 5 passes.
5. Equivalent ml-pass corect.
6. CNC operation rows din `operation_rows`, nu legacy aggregated catalog.
7. `face_and_backing_cnc_cut` nu este sursă de cantități CNC.
8. CNC rates pot rămâne `missing_rate` dacă neimplementate.

---

## 11. LED confirmations

Dacă se atinge lighting / geometry / emblem:

1. LED exterior perimeter corect.
2. Letter modules corecte.
3. Emblem `area_lit` corect.
4. Total modules = letters + emblem când emblem `area_lit`.
5. W = modules × 1.44.
6. PSU required = W × 1.30.
7. PSU propus respectă catalogul.
8. PBL `area_lit`: total modules = 59, W = 84.96, PSU = [160].
9. Raster/artwork nu generează LED perimeter.

---

## 12. Material Breakdown confirmations

1. Materiale nu lipsesc.
2. Materiale nu duplicate greșit.
3. Materiale pe layer se adună corect.
4. Serii diferite rămân separate.
5. Consumabile separate de materiale.
6. Operații separate de materiale.
7. Print/laminare preview dacă pricing incomplet.
8. `pricing_status=missing_rate` când nu există tarif.
9. `estimated_cost=null` când nu există preț.
10. `consumes_stock_now=false` pentru preview.
11. `creates_task_now=false` pentru preview.
12. Registry override policy respectată.
13. Owner source guard respectat.

---

## 13. Operator UI confirmations

1. Layer table: rânduri corecte.
2. Kind/source vizibil: Corel layer / Pseudo-layer / Raster artwork.
3. **Metric labels by source:** Corel curve length (layer-sum), LED exterior only, CNC cut perimeter, cant/return material — never display LED as the primary curve length without the Corel-comparable row when face geometry exists.
4. Production **part count** must not be labeled as typographic “litere” without grupuri/piese/caractere context.
5. Role labels operator-friendly (Față litere, Artwork / print / autocolant).
6. Confirm all nu confirmă greșit unknown low confidence.
7. Confirm all nu lasă `missing` dacă toate confirmabile.
8. Warninguri vizibile.
9. Pending/manual split vizibil când e cazul.
10. Material Breakdown reîncarcă după save sau pending-save banner.
11. Unități corecte: **m** și **m²** pentru lungimi/suprafețe; **ml** doar pentru adeziv/lichide; **m-pass** pentru echivalent utilaj CNC — **UI operator must not use ml for linear meters**.
12. **UI operator must not expose raw internal IDs** (`_220…`); folosește labeluri semantice (logo stânga/dreapta).
13. **Debug keys must be hidden by default** (mapping_gap, dryrun_task_key, missing_client_analysis_hash etc.) în accordion „Detalii tehnice / debug”.
14. **CNC, print, laminare, colantare must be separate operation categories** în preview ofertare.
15. **Informative material estimate must not look like final quote price** — wording „Estimare internă materiale — informativ”, nu „Total estimat materiale (ofertă)”.
16. Readiness separat: preview ofertare vs handoff real vs generare task reală.
17. Logo raster extern lipsă: placeholder/warning controlat, nu broken icon singur.

---

## 14. Runtime smoke confirmations

Pentru builduri mari, minim:

1. PBL browser smoke.
2. Ana Maria layered browser smoke.
3. Ana Maria unlayered browser smoke.
4. Workspace real de bug dacă build repară bug raportat.
5. Restore workspace după smoke.
6. Stack health: backend healthy, frontend healthy, live code = HEAD.

**Automated smoke:** `frontend/e2e/intake-v4-analyzer-regression-gate-smoke.spec.ts` (cu `PW_SKIP_WEB_SERVER=1` când stack rulează).

Dacă runtime smoke nu este rulat, verdictul maxim este **PASS scoped** / **HOLD push**.

---

## 15. Scope safety confirmations

La final, confirmă:

1. No push (dacă nu a fost cerut).
2. No quote/order/tasks.
3. No ExecutionPlan.
4. No tasks_json.
5. No stock consumption.
6. No Pricing Registry changes.
7. No Pricing Registry rewrite.
8. No Color Registry changes.
9. No Color Registry rewrite.
10. No CostEngine changes.
11. No employee assignment.
12. No cleanup global.
13. No deleted untracked.
14. No unrelated files committed.

---

## 16. Final verdict rules

| Verdict | Meaning |
|---------|---------|
| **PASS** | Toate testele + smoke + checklist OK. |
| **PASS scoped** | Cod/teste OK, dar smoke sau parte din matrice nerulată. |
| **HOLD push** | Tracked dirty, lipsă smoke, regressions, confirmări incomplete. |
| **FAIL** | Fixture nou nu merge sau PBL/regression gate pică. |
| **NO PUSH** | Tracked dirty, test failed, smoke failed, remote/head mismatch. |

---

## 17. Standard final report format

Fiecare raport final trebuie să includă:

1. Verdict.
2. Branch.
3. HEAD before.
4. HEAD after.
5. Remote HEAD before.
6. Remote HEAD after (dacă push).
7. Files modified.
8. Commit hash.
9. Git status final.
10. Tests run.
11. Runtime smoke run.
12. Fixture matrix result.
13. PBL result.
14. Ana Maria layered result.
15. Ana Maria unlayered result.
16. Material Breakdown result.
17. Pricing result.
18. CNC/LED/edge result (dacă relevant).
19. UI result.
20. Docs updated.
21. Remaining gaps.
22. Recommendation push/hold.
23. Scope safety confirmations.

---

## Quick command bundle

```powershell
# Frontend analyzer gate
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts

# Full frontend matrix (recommended)
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts src/lib/svgAnalyzer/analyzer/pblLayerePseudoLayerGuard.test.ts src/lib/svgAnalyzer/analyzer/ana-maria-layer-roles.test.ts src/lib/intakeV4/intakeV4LayerRoleDisplay.test.ts

# Backend pricing guards
cd ..\backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_layer_finish_pricing_matrix.py tests/test_intake_v4_oracal_641_651_pricing.py -q

# UI smoke (stack on :8000 + :3000)
cd ..\frontend
$env:PW_SKIP_WEB_SERVER='1'
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-analyzer-regression-gate-smoke.spec.ts
```
