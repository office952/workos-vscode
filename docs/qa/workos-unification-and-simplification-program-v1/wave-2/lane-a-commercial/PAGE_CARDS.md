# Lane A — Wave 2 page cards (primary owner)

Role: COMMERCIAL_SPINE. Runtime: `wave-2/runtime/rt-capture-log.json`. No product writes.

## `/intake` — Cereri

| Field | Value |
|-------|--------|
| PURPOSE | List + select cereri; pipeline counts; open V6 |
| PRIMARY USER | sales / admin / manager |
| PRIMARY DECISION | Which request to open next |
| SYSTEM OWNER | Intake list (not Product Truth) |
| READS | intakes API / Live DB (55 cereri) |
| WRITES | create / status / draft-quote — **not executed** |
| UPSTREAM | clients (display) |
| DOWNSTREAM | `/intake-v6/:id/operator` |
| Disposition proposal | KEEP + SIMPLIFY (pipeline vs list vs detail density) |

Runtime: list + row-selected, light/dark, sales light. Scroll PASS 0→723. `+ Cerere Nouă` observed, not clicked.

Block classification: pipeline cards USER_NEEDED; raw `IR-*` + `NORMAL` + `email` channel OPERATOR_NEEDED / TECHNICAL; FLUX Produse ADMIN/TECHNICAL (wrong grain for this page).

## `/intake-v6/IR-MSRB28PU/operator` — Intake V6

| Field | Value |
|-------|--------|
| PURPOSE | Confirm product/finish truth then handoff to offer |
| PRIMARY USER | operator of volumetric request |
| PRIMARY DECISION | Are finishes/offer data confirmed enough to hand off? |
| SYSTEM OWNER | Intake V6 workspace / Product Truth confirmation |
| READS | workspace hydrate |
| WRITES | persist / handoff — **not executed** (confirm blocked) |
| UPSTREAM | `/intake` edit |
| DOWNSTREAM | `/quotes/:code` (blocked on this fixture) |
| Disposition proposal | KEEP + SIMPLIFY (commercial rail + technical disclosure stacked) |

Opened via existing list row — no bootstrap `/intake-v6/operator`. Header showed **IV6-F823AA06** while URL/list id is **IR-MSRB28PU** (identity contradiction).

Steps: Straturi / Configurare (Finisaje, Iluminare, **Panou / carcasă**, Montaj) / Confirmare.

Gap closure: **Straturi proven** (`Pasul 1 din 3 - straturi`, layers panel, file `test-bond-litere.svg`, 2 straturi confirmed). Original `layers/` shots are Configurare (SUPERSEDED_MISLABEL). **Panou / carcasă opened** (`aria-selected=true`; Alucobond form + blockers). Confirm: handoff disabled, 1 blocker. Commercial rail “OFERTĂ CLIENT” 725,25 EUR visible on Configurare.

Block classes: step nav USER_NEEDED; finish anatomy USER_NEEDED; OFERTĂ CLIENT rail OPERATOR_NEEDED but money-authority risk; “Detalii tehnice despre finisaj” / diagnostic ADMIN/TECHNICAL; line-count “25 linii” TECHNICAL.

## `/orders` + `/orders/ORD-IV6-V2-1786318810-31`

| Field | Value |
|-------|--------|
| PURPOSE | Accepted snapshot + execution state; no re-price |
| PRIMARY USER | commercial + ops viewer |
| PRIMARY DECISION | Which order to inspect / dispatch |
| SYSTEM OWNER | Order snapshot (not CPP) |
| READS | orders + execution observability |
| WRITES | generate plan — **not executed** |
| UPSTREAM | quote convert |
| DOWNSTREAM | `/execution/:id`, `/quotes` |
| Disposition proposal | KEEP; RENAME “Înghețat” vs operator language TBD |

28 orders; 27 Înghețat; value 34.331,97 RON (currency ≠ quote EUR). Dual flux strips (commercial + execution). Empty detail CTA “Vezi produse” → Product System (edge recorded, not traversed).

## `/clients` + `/clients/SC CLIENT NOU SRL`

| Field | Value |
|-------|--------|
| PURPOSE | Client registry + 360 activity |
| PRIMARY USER | sales |
| PRIMARY DECISION | Which client’s spine to open |
| SYSTEM OWNER | Client registry (weak: “1 în registrul entități” vs 19 cards) |
| READS | merged clients + intakes/quotes/orders |
| WRITES | fiscal verify — **not executed** |
| UPSTREAM | none (lateral) |
| DOWNSTREAM | intake/quotes/orders tabs |
| Disposition proposal | KEEP + MOVE into commercial story (not only Relații) |

19 clients; most “fără identificare fiscală”. Tabs Cereri (8 scroll segs), Oferte, Comenzi (empty/short). Stub tabs Facturi/Documente/Note/Timeline: STATE_NOT_REACHED (disabled/not opened).

## `/quotes` — observe only

Wave 1 owns the page card. Edges: quote → V6 (`IV6-734601c4-…`); quote → `/orders`; quote → client **no link** (DEAD_END).
