# Intake V4 Operator Form UI Audit - 2026-06-26

## Scope

Route audited visually: `/intake-v4/9fe22974-1f65-4bce-847d-02d74bb16e05/operator`

File/workspace context: `gradi-curat.svg`, template `TPL-VOLUMETRIC-LETTERS`.

This audit covers the operator form shape for steps 1, 2, and 3. It does not change runtime code.

Target device: desktop operator workstation only. Mobile is not a product target for this flow.

## Protected Behaviors

- Step 3 must not display `Goluri` or `interioare`.
- `Spate litere` must not expose `Fără spate` / `Fara spate`.
- Live calculation must keep `Oracal 651`, `Oracal 8500`, and `Oracal 651 / cant volum` separate.
- Review must show `Translucent` checked for `logo stânga` and `logo dreapta`.
- LED must be enabled by default, with `Module LED`, `0.75 W / modul`, and neutral light.
- Emblem lighting must be separated from letter lighting.
- Mounting template area must be displayed as square meters.
- CNC rows and template-related costs must be visible in the live ledger.
- Upload controls should show Romanian labels, not native browser text like `Choose File`.

## Existing UI Findings

The original flow was functionally close, but it behaved visually like a technical workspace plus summary panels, not like a controlled production form.

Weak areas found:

- Step 1 layer classification was too technical and not framed as a production decision.
- Step 2 was too tall because every group expanded into a full row block.
- Letter groups and emblem groups shared similar controls, but their business meaning was not visually separated enough.
- The live calculation mixed aggregate totals and material lists instead of one clear ledger.
- Step 3 mixed summary/report language with confirmation language.
- The draft boundary needed to be explicit: internal draft only, not client send, not production order, not inventory consumption.

## Redesign Delivered

The first static demo was replaced with a more complete desktop operator cockpit:

- Integrated WorkOS-style left menu with `Operator` active.
- Dense job command header: file, dimensions, canonical perimeter, and template area.
- Smart cockpit with current step, active production zone, auto-confirmation, calculation impact, and protected rules.
- Step 1 layer classification with SVG preview, layer list, and selected-layer inspector.
- Step 2 finish form grouped by production zone: `Litere`, `Embleme / logo`, `Template + spate`, and `LED`.
- Step 3 confirmation gates with a clear internal-draft boundary.
- Sticky right ledger with filters for `Toate`, `Materiale`, and `Operații`.

Files:

- `docs/mockups/intake-v4-operator-form-demo.html`
- `docs/mockups/intake-v4-operator-redesign-schema.md`
- Desktop copy: `C:\Users\offic\Desktop\intake-v4-operator-form-demo.html`

## Verification

Demo checks run on the served HTML page with Chrome:

- Desktop viewport: `1440 x 950`.
- Desktop viewport: `1280 x 900`.
- No horizontal overflow on desktop at `1440` or `1280`.
- WorkOS menu is present and `Operator` is active.
- Step switching works: `Layere`, `Finisaje`, `Confirmare`.
- Finish zone switching works: `Litere`, `Embleme / logo`, `Template + spate`, `LED`.
- Live ledger shows 18 rows on `Toate`.
- Ledger rows are clickable and update the `Impact calcul` card.
- No mojibake sequences found in the rendered HTML.
- Demo does not display `Goluri` or `interioare`.
- Demo does not display `Fără spate` / `Fara spate`.
- Ledger splits `Plexiglas 3 mm / față litere`, `Plexiglas 3 mm / embleme/logo`, `Oracal 651 / față litere`, `Oracal 8500 / față litere`, and `Oracal 651 / cant volum`.
- CNC rows are visible: `CNC debitare plexiglas` and `CNC debitare Forex`.
- LED default is visible as `0.75 W neutral`.
- Upload controls use Romanian labels instead of native browser text like `Choose File`.

Saved review screenshots on Desktop:

- `intake-v4-operator-redesign-1440.png`
- `intake-v4-operator-redesign-1280.png`
- `intake-v4-operator-redesign-layers.png`

Served preview:

- `http://127.0.0.1:4177/intake-v4-operator-form-demo.html`
- Static server entrypoint: `docs/mockups/serve-mockups.mjs`
