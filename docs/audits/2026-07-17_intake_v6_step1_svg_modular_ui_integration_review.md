# Owner review — Intake V6 Step 1 SVG modular UI integration

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| GO | `OWNER_REVIEW_INTAKE_V6_STEP1_SVG_MODULAR_UI_INTEGRATION` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `26eb0c7` (lineage: `62dc7a7` → `773b4f1` → `26eb0c7`) |
| Start | `INTAKE_V6_SVG_MODULAR_UI_REVIEW_IN_PROGRESS` |
| Verdict | **`DUAL_UI_FLOW_STILL_VISIBLE`** |
| Dual-flow class | **`SINGLE_SOT_BUT_DUPLICATED_UI`** |
| App edits | **None** |
| Commit | **None** |

## Mini decizia mea

Nu adăuga un al doilea sistem vizual sub UI-ul matur de layere. Modularitatea Product System există și binding SoT este unificat — dar Pasul 1 încă arată **două flow-uri vizuale**: carduri layer (legacy roles) + panou „Asocieri produs” (+ ACP nested).

---

## 1. Existing modularity map

| Nivel | Contract existent | Sursa | Runtime proof | Vizibil în UI | Gap real |
|-------|-------------------|-------|---------------|---------------|----------|
| Product Template | `TPL-VOLUMETRIC-LETTERS_v2` | registry / availability | API 200, item present | Cod în helper + țintă pe carduri | Nu e problemă |
| Component Template | FACE / LOGO / ACM / METAL | `svg_component_binding_contract.py` | `svg_bindable_components` ×4 | Listă în panoul nou (coduri mono) | Expunere fragmentată |
| Interface Contract | FACE_CANT, BACK_SUPPORT, … | `volumetric_letters_v1.py` | process contracts | **Nu** în Step 1 | Ascuns (OK pentru Step 1) |
| SVG binding | geometry roles + selection modes | binding contract + availability | payload verified | Parțial (panel) | Nu pe carduri layer |
| FinishSetup | `svg_component_bindings` + `svg_support_selection` | `intake_v4.py` | tests PASS | Indirect (după save) | OK |
| ProductDefinition | `svg_component_instances` | PD builder | tests PASS | Nu în Step 1 | OK |
| ProductAggregate | support XOR metal/ACM | aggregate / process | not Step 1 surface | Nu | N/A Step 1 |
| Legacy adapter | `LEGACY_INTAKE_SVG_ROLE_ADAPTER` | `intakeV6LayerRoleOptions.ts` | dropdown Vector Litere/Logo | **Da — domină cardurile** | **Maschează modularitatea** |

**Concluzie modularitate:** există și e coerentă în backend/read model. Nu lipsește. UI-ul o proiectează **incomplet și duplicat**.

---

## 2. Runtime / API proof (Product System)

- **Endpoint:** `GET /api/v1/product-system/template-availability?include_runtime_modules=true` → **200**
- **Template:** `TPL-VOLUMETRIC-LETTERS_v2`
- **Bindables (4):**
  1. Vector litere → `TPL-VOLUMETRIC-FACE_v1` · `LETTER_VECTOR_SET` · required · active default
  2. Vector logo → `TPL-VOLUMETRIC-LOGO_v1` · guarded candidate · inactive default
  3. Panou Alucobond casetat → `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` · `SUPPORT_CONTOUR` · `CLOSED_CONTOUR` · max 1 · optional · inactive default
  4. Structură metalică · SVG binding disabled

Panoul FE apelează același API (`productTemplateAvailabilityApi.list`) — **nu** hardcodează lista ACP.

---

## 3. Mount order (Step 1 main column)

```text
1. IntakeV6LayersFileConfirmPanel     (preview + metrics + hover layer)
2. ArtworkOnlyDecision (conditional)
3. IntakeV6LayersRoleTable cards      (LEGACY role dropdown + Țintă Product System)
4. IntakeV6SvgComponentAssignmentPanel  ← NEW, below cards
     ├─ bindable list (PS)
     ├─ sync litere/logo button
     └─ Contur suport → IntakeV6AlucobondContourPanel (full casing UI)
5. ProductCompositionPanel
6. OfferScopePanel
7. Technical details accordion
```

Route shell: `/intake-v6/:workspaceId/operator` · step `layers`.

---

## 4. Existing layer UI — strengths

| Strength | Evidence |
|----------|----------|
| Mature file/preview | `IntakeV6LayersFileConfirmPanel` |
| Layer cards + hover | `IntakeV6LayersRoleTable` + `highlightedLayer` |
| Contour overlay already wired | `contourOverlay` from `selectedContourId` into preview |
| Color / layer grouping | analyzer + table layouts |
| Progress / confirm-all | operator panel |

**Reusable for closed contour:** same preview + overlay path already exists (`contourOverlay`). Do **not** invent a second preview.

**Hardcoded / legacy:** dropdown uses only `INTAKE_V6_OWNER_LAYER_ROLE_OPTIONS` (Vector Litere / Vector Logo). Card shows `Țintă automată Product System: TPL-…` — Product Template code as primary owner signal.

---

## 5. New panel audit

| Question | Answer |
|----------|--------|
| Unde? | Sub layer decision band, înainte de composition/offer |
| De ce? | Consume PS bindables + nest ACP |
| Ce afișează? | Lista componente + sync button + panou ACP complet |
| Ce dublează? | Litere/logo (deja pe carduri); confirmări; status asociere |
| Authority? | PS availability (corect) |
| Vizibil cu layer selectat? | **Nu** pe același card — context separat, mai jos |
| Al doilea sistem vizual? | **Da** |

### Duplicate table

| Element nou | Echivalent existent | Duplicat? | Authority | Recomandare |
|-------------|---------------------|-----------|-----------|-------------|
| Lista bindable „Vector litere” | Card layer + dropdown Vector Litere | **Da** | PS list vs legacy role | Merge pe card |
| Buton sync litere/logo | Confirm role pe card / confirm-all | **Da** | bindings vs layer_role_setup | Un singur confirm |
| Contur suport + Alucobond panel | Preview overlay + (fost) panel separat | Parțial | bindings SoT OK | Progressive pe geometrie selectată |
| Coduri `TPL-…` mono | Badge „Țintă Product System” | **Da** | noise | Secundar / tooltips |
| Guards text lung | Warnings layer | Noise | PS | Collapse |

---

## 6. Dual-flow verdict

| Check | Result |
|-------|--------|
| Visual flows | **A** layer cards (legacy roles) + **B** Asocieri produs (+ ACP) |
| Persistence SoT | **Single** (`svg_component_bindings` + synced selection) |
| Confirmations | Multiple (layer role, sync button, ACP confirm) |
| Same element twice | Layer as role + again as binding status |
| Classification | **`SINGLE_SOT_BUT_DUPLICATED_UI`** / dual visual flow |

Legacy adapter **masks** modularity: operator still thinks in „Vector Litere/Logo pe card”, then must learn a second „Asocieri produs” step.

---

## 7. Role vs component / available vs active

| Concept | Owner-facing today | Issue |
|---------|-------------------|-------|
| Rol geometric | Vector Litere / Logo pe card; Contur suport în panel | Split across UI regions |
| Componentă | Panou Alucobond + listă PS | Clear in panel; absent on cards |
| Product Template code | Prominent on cards + panel helper | Too loud |
| Available vs active | „Optional · inactiv implicit” | Good label |
| ACP config timing | Alucobond panel mounts whenever `supportComp` exists and contours detected | **Config UI too early** — appears as soon as available, not only after contour association |

---

## 8. Hover / support contour

| Capability | Status |
|------------|--------|
| Layer hover → preview highlight | Existing, good |
| Contour selection → overlay | Wired (`contourOverlay` → preview) |
| Same overlay system | Yes — reuse, don't duplicate |
| Contour as first-class card type | **Missing** — only in nested ACP list |

**Best visual integration:** treat Contur suport as a geometry card/row in the same decision band; reuse overlay; expand casing only after association.

---

## 9. Hierarchy & density

Desired: Geometry → Role → Component → Config.  
Actual: Geometry+Role on cards → **then** Component list → Config ACP → composition/offer. Hierarchy is **split**; config ACP appears before a clear „active” state.

Density (from mount stack / `space-y-4`, not live pixel capture):

| Viewport | Finding (layout inference) |
|----------|----------------------------|
| 1920×1080 | Usable but long scroll; assignment + ACP below fold after cards |
| 1440×900 | CTA continue / footer likely compete with long stack |
| 1366×768 | High scroll; dual panels hurt comprehension |

**Screenshot evidence:** GUARDED — no browser automation MCP / no seeded workspace write this pass. Structure proven from code mount order + live availability payload. FE/BE `:3000`/`:8001` up.

---

## 10. Owner comprehension (≤10s)

| Question | Clear in current UI? |
|----------|----------------------|
| Ce strat selectez? | Yes (cards) |
| Ce reprezintă? | Partial (legacy role) |
| Ce componentă PS? | **No** on card — only after scrolling to panel |
| Obligatoriu/optional? | Partial on panel only |
| Geometrie evidențiată? | Yes (hover/overlay) |
| Confirmat? | Ambiguous (role vs sync vs ACP) |
| Ce lipsește / pot continua? | Layer gate clear; binding sync easy to miss |

→ **`OWNER_COMPREHENSION_FAIL`** for the modular story (not for basic layer roles).

---

## 11. Real fixture (`LITERE-VOLUMETRICE-ACP.svg`)

| Item | Expectation from prior proofs |
|------|-------------------------------|
| Letter paths / color groups | Layer cards |
| Outer polygon panel | Closed-contour candidates in ACP subsection |
| Natural fit in same UI? | **Yes** — as Contur suport geometry row, not second page region |

SHA unchanged policy: external file not touched this review.

---

## 12. Single recommendation

**Reuse existing layer/geometry cards** → show geometry type + PS component on the **same card** → shared hover/overlay → ACP casing only after Contur suport confirmed.

Do **not** keep a second full „Asocieri produs” stack as the primary operator surface. Keep binding SoT / FinishSetup / PD as-is.

---

## 13. Small-fix scope (if Option 2)

1. Move component label + status onto layer/contour cards.  
2. One confirmation path (no separate sync CTA as primary).  
3. Contur suport as geometry type in decision band.  
4. Progressive disclosure for casing.  
5. Demote raw `TPL-*` codes.  
6. Keep `svg_component_bindings` / FinishSetup / PD unchanged.

**Must remain:** PS availability authority, binding SoT, FinishSetup durability, PD instances, contour overlay.  
**Must move/merge:** assignment panel content into cards.  
**Must not rebuild:** nest2 analyzer, Product System contracts, modularity model.

---

## 14. Tests (read-only)

| Suite | Result |
|-------|--------|
| FE `svgComponentBindings` + Step 1 | 14 PASS |
| BE binding contract + persistence | 8 PASS |
| Live screenshots / seeded WS E2E | Coverage gap (guarded) |

---

## 15. Dead pieces (report only)

- Visual duplicate: bindable list vs layer role cards  
- Legacy dropdown as primary owner control  
- „Țintă automată Product System” Product Template codes on cards  
- Extra sync button  
- Full ACP config while component still „inactiv implicit”  
- Raw technical codes + guards dump in list  
- Composition panel still below (third product-ish surface)

---

## 16. Next safe step

**Option 2 — GO SMALL INTAKE V6 SVG UI UNIFICATION FIX**

(Not Option 1 accept-as-is — dual visual flow remains.)

## Roadmap

Awareness **9/10** · Direction **88/100%** (backend modular path solid; UI integration incomplete)

---

## SMALL UI UNIFICATION IMPLEMENTATION RESULT

| Field | Value |
|-------|-------|
| GO | `SMALL_INTAKE_V6_SVG_UI_UNIFICATION_FIX` |
| HEAD before | `a8737c0` (audit docs) / feature base `26eb0c7` |
| Verdict | **`INTAKE_V6_SVG_UI_UNIFICATION_COMPLETE_WITH_GUARDS`** |
| Dual-flow class after | **`SINGLE_VISUAL_FLOW`** (SoT still single) |
| Backend / PS / FinishSetup / PD | **Unchanged** |

### What changed (UI only)

1. Layer cards show **Rol geometrie** + **Componentă produs** (PS bindable) on the same card.
2. Removed primary „Țintă automată Product System: TPL-…”.
3. Technical codes under **Detalii tehnice**.
4. Letter/logo bindings **auto-sync** from layer confirmation (no separate sync CTA).
5. **Contur suport** card in the same grid (`IntakeV6SupportContourGeometryCard`).
6. ACP casing = progressive (only after contour + Panou Alucobond selected).
7. Former assignment panel → compact **Rezumat asocieri** (`data-variant="summary"`).

### Runtime proof

| Item | Result |
|------|--------|
| URL | `http://127.0.0.1:3000/intake-v6/9c05851e-3230-4a97-821b-e52293ada844/operator` → Straturi |
| Workspace | `IV6-4DD49A26` / `TPL-VOLUMETRIC-LETTERS_v2` |
| Fixture | `LITERE-VOLUMETRICE-ACP.svg` (uploaded for contour proof; file not modified) |
| Layer cards | 3–6 with component blocks; logo **Guarded** |
| Support card | Present when `closedContourCandidates` exist |
| Sync button | Absent |
| Summary | Compact, not primary flow |
| CTA | Continuă la Configurare visible |
| Screenshots | `docs/audits/screenshots/2026-07-17_intake_v6_svg_ui_unification/` |

### Guards remaining

- Support contour card absent until closed-contour candidates exist on the analyzer report.
- Legacy role dropdown remains as geometry bridge (contained, not PS authority).
- Full ACP confirm → save → refresh → PD instance path not re-owned in this UI-only build (SoT unchanged; prior durability tests still PASS).
- Real workspace was used for visual proof (file swap on existing WS).

### Tests / build

| Gate | Result |
|------|--------|
| FE bindings + RoleTable + Step 1 + closed-contour | 30 PASS |
| BE binding contract + persistence | 8 PASS |
| `pnpm build` (frontend) | PASS |

### Next safe step

**Option 1 — OWNER REVIEW OF UNIFIED INTAKE SVG UI**

---

## SVG CARD UX RESTORE (post owner screenshot)

| Field | Value |
|-------|-------|
| GO | `RESTORE_EXISTING_SVG_CARD_UX_WITH_ACP` |
| Verdict | **`EXISTING_SVG_CARD_UX_RESTORED_WITH_ACP`** |
| Dual-flow class after | **`SINGLE_VISUAL_FLOW`** — ACP uses the same card model as layers |
| Screenshots | `docs/audits/screenshots/2026-07-17_intake_v6_svg_card_ux_restore/` |

### Delta vs SMALL UI UNIFICATION

- Assignment summary (**Rezumat asocieri**) removed from Step 1 primary surface.
- ACP is no longer an Alucobond candidate-list / Confirmă selecția / embedded-casing panel; it is **`Panou ACP — contur exterior`** in the layer card grid.
- Composition recommendation SoT extended to honor `svg_component_bindings` / `svg_support_selection` for support without requiring a layer role.
- Owner-facing composition label: **Panou Alucobond casetat**.

### Runtime re-proof

Workspace `IV6-4DD49A26` + `LITERE-VOLUMETRICE-ACP.svg` on FE `:3000` / BE `:8001`: layer cards + ACP card same grid; no Rezumat asocieri; no permanent 21-candidate list; composition `letters_plus_logo_plus_support` after association. See worklog § SVG CARD UX RESTORE.
