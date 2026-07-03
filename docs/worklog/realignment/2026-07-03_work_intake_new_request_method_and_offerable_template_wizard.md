# Work Intake new request method and offerable template wizard

Data: 2026-07-03
Scope: implementare controlata pentru `Cerere Noua -> Modalitate ofertare -> Template-uri active pentru ofertare -> Intake V6 workspace`. Fara quote, fara order, fara execution, fara inventory, fara pricing, fara seed, fara migration.

## 1. Context

Product System availability API este acum sursa de adevar pentru ce template poate fi ales initial in ofertare. Work Intake trebuia sa nu mai porneasca direct din client/tip lucrare si sa nu aleaga implicit template-ul V6 fara context de metoda si template selectat.

Flow implementat:

```txt
Cerere Noua
-> Pas 1: Modalitate ofertare
   SVG Analyzer - Intake V6
-> Pas 2: Template Product System
   Template-uri active pentru ofertare din backend availability API
-> Pas 3: Client + detalii cerere
-> Creeaza/ensure Intake V6 workspace
   offer_method + selected_template_code + source
```

## 2. Availability API folosit

Frontend `NewIntakeDialog` foloseste:

```txt
GET /api/v1/product-system/template-availability?offerable_only=true&include_runtime_modules=false&include_archived=false
```

Adapter frontend:

```txt
productTemplateAvailabilityApi.list({
  offerable_only: true,
  include_runtime_modules: false,
  include_archived: false,
})
```

Lista afisata este filtrata suplimentar pe `quote_offerable === true`.

## 3. Pas 1 Modalitate ofertare

Pasul 1 este explicit `Alege modalitatea de ofertare` si contine prima metoda activa:

```txt
SVG Analyzer - Intake V6
offer_method = svg_analyzer_intake_v6
```

Continuarea este blocata pana cand metoda este selectata.

## 4. Pas 2 Template-uri active/ofertabile

Pasul 2 se numeste `Alege template-ul Product System` si sectiunea principala este `Template-uri active pentru ofertare`.

Template-urile sunt afisate din backend availability API, nu din mock data si nu din lista UI hardcodata. Runtime modules raman disponibile intern in Product System, dar nu apar ca produs initial ofertabil.

## 5. Regula de naming

In UI-ul modificat se foloseste `active pentru ofertare` / `ofertabile`. Termenii blocati de owner nu sunt folositi in fisierele curente modificate pentru flow.

Verificare:

```powershell
grep workspace pe NewIntakeDialog, WorkIntake, Intake V6 service/teste pentru termenii blocati
```

Rezultat: PASS, fara match in fisierele curente ale build-ului.

## 6. Backend contract selected_template_code

Contractul V6 ensure accepta acum:

```txt
offer_method
selected_template_code
source
```

Pentru `source = work_intake_new_request`, `selected_template_code` este obligatoriu. Backendul valideaza template-ul prin `ProductTemplateAvailabilityService` si respinge runtime modules sau template-uri neofertabile cu 422.

Contextul este persistat in payload-ul workspace-ului:

```txt
offer_method
selected_template_code
source
work_intake_context.selected_template_is_initial = true
work_intake_context.product_truth_final_decided_later = true
```

## 7. Ce hardcoding a fost eliminat/controlat

- Work Intake new request nu mai depinde de hardcoding UI pentru template-uri ofertabile.
- V6 ensure pentru `work_intake_new_request` nu mai foloseste direct fallback-ul `TPL-VOLUMETRIC-LETTERS_v2`; cere template selectat si il valideaza prin availability.
- Fallback-ul legacy ramane controlat doar pentru apeluri non-Work-Intake-new-request, ca sa nu rupem trasee vechi in afara scope-ului.

## 8. Teste rulate

```powershell
Set-Location "C:\Users\offic\workos_app_vs\backend"
& "C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe" -m pytest tests/test_intake_v6_workspace_offer_context.py -q
```

Rezultat: PASS, `3 passed, 3 warnings`.

```powershell
& "C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe" -m py_compile "C:\Users\offic\workos_app_vs\backend\schemas\intake_v4.py" "C:\Users\offic\workos_app_vs\backend\schemas\intake_v6.py" "C:\Users\offic\workos_app_vs\backend\routers\intake_v6_workspaces.py" "C:\Users\offic\workos_app_vs\backend\services\intake_v6_workspace_service.py" "C:\Users\offic\workos_app_vs\backend\tests\test_intake_v6_workspace_offer_context.py"
```

Rezultat: PASS, fara output.

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"
npx.cmd --yes pnpm@8.10.0 exec vitest run src/components/workos/NewIntakeDialog.test.tsx
```

Rezultat: PASS, `1 file, 7 tests`. Vitest afiseaza warning-uri existente de `act(...)` pentru state updates async in dialog.

```powershell
Set-Location "C:\Users\offic\workos_app_vs\frontend"
npx.cmd --yes pnpm@8.10.0 exec tsc --noEmit --project tsconfig.app.json --pretty false
```

Rezultat: PASS, fara output.

Selector cerut:

```powershell
Set-Location "C:\Users\offic\workos_app_vs\backend"
& "C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe" -m pytest tests -k "intake_v6 and workspace" -q
```

Rezultat: BLOCKED by existing collection debt, nu de build-ul curent:

- `ModuleNotFoundError: No module named 'create_release_package'`
- `ImportError: cannot import name 'IntakeV4LayerBindingContract' from 'schemas.intake_v4'`

## 9. Runtime verification

Runtime verificat in browser pe Vite izolat:

```txt
http://127.0.0.1:3001/intake
```

Nota: serverul existent de pe `3000` era disponibil, dar click-ul pe `Cerere Noua` nu deschidea modalul in tabul existent. Pentru verificarea sursei curente am pornit un Vite separat pe `3001` cu `VITE_API_BASE_URL=/api`, folosind proxy-ul Vite catre backend `8000` si evitand CORS.

Rezultat UI:

- Pas 1 apare primul: `Pas 1/3`, `Alege modalitatea de ofertare`.
- `SVG Analyzer - Intake V6` este activ.
- Continuarea este disabled pana la selectarea metodei.
- Pas 2 afiseaza `Template-uri active pentru ofertare`.
- `TPL-VOLUMETRIC-LETTERS_v2` apare ca template ofertabil.
- `TPL-VOLUM-ALUMINIU_v1` nu apare in Pas 2.
- Termenii blocati de naming nu apar in Pas 2.
- Pas 3 afiseaza sumarul `Template Product System` si creeaza cererea doar dupa client + descriere.
- Dupa fixul de routing, creare request navigheaza la:

```txt
http://127.0.0.1:3001/intake-v6/b003002e-5162-4ea8-9fe5-2a2598f50e9d/operator
```

Workspace creat:

```json
{
   "id": "b003002e-5162-4ea8-9fe5-2a2598f50e9d",
   "workspace_code": "IV6-3B889E69",
   "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
   "offer_method": "svg_analyzer_intake_v6",
   "selected_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
   "source": "work_intake_new_request",
   "work_intake_context": {
      "offer_method": "svg_analyzer_intake_v6",
      "selected_template_code": "TPL-VOLUMETRIC-LETTERS_v2",
      "source": "work_intake_new_request",
      "selected_template_is_initial": true,
      "product_truth_final_decided_later": true
   }
}
```

Count-uri quote/order/execution/inventory inainte si dupa creare au ramas identice:

```json
{
   "execution_observation_config": 1,
   "execution_plan": 2,
   "execution_reality": 0,
   "inventory_material_price_history": 17,
   "inventory_material_source_review_audit": 5,
   "inventory_materials": 63,
   "inventory_sheet_remediation_audit_events": 0,
   "order_output_snapshot_references": 0,
   "orders": 4,
   "quote_documents_archive": 0,
   "quote_output_snapshots": 2,
   "quote_snapshots_v2": 4,
   "quotes": 21
}
```

## 10. Ce NU am modificat

- pricing;
- Quote/Order;
- Intake V6 flow comercial intern;
- SVG Analyzer intern;
- Product Truth;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- Employee Mobile;
- Inventory;
- seed-uri;
- migration;
- DB manual.

## 11. Riscuri ramase

- Exista debt de collection in backend tests care blocheaza selectorii largi.
- Vitest pentru dialog afiseaza warning-uri `act(...)`; testele trec, dar o curatare separata poate imbunatati ergonomia suitei.
- Fallback-ul legacy `TPL-VOLUMETRIC-LETTERS_v2` ramane pentru apeluri non-new-request ca masura de compatibilitate.
- Serverul existent de pe `3000` poate avea bundle/state stale; runtime final a fost verificat pe server izolat `3001` cu sursa curenta si proxy `/api`.

## 12. Next safe step

Urmatorul pas sigur este repornirea serverului principal `3000` cu acelasi API base/proxy curat, apoi un smoke scurt pe portul canonic pentru operator. Functional, flow-ul nou este verificat pe sursa curenta.