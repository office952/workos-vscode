# Lane H — navigation / journeys (no page cards)

## Actual followed edges (RT)

| FROM | CONTROL | TO | HONESTY | CONTEXT |
|------|---------|-----|---------|---------|
| `/intake` | Deschide Intake V6 | `/intake-v6/IR-MSRB28PU/operator` | GOOD_EDGE | Header then shows IV6-F823AA06 — CONTEXT_LOSS / identity |
| `/orders` | select card | `/orders/ORD-IV6-V2-1786318810-31` | GOOD_EDGE | URL sync |
| order detail | Oferte | `/quotes` | GOOD_EDGE | list not same quote guaranteed |
| `/clients` | row | `/clients/SC CLIENT NOU SRL` | GOOD_EDGE | |
| `/quotes` | din cerere IV6-734601c4-… | `/intake-v6/734601c4-…/operator` | GOOD_EDGE | different workspace than IR-MSRB28PU |
| `/quotes` | Comenzi | `/orders` | GOOD_EDGE | list |
| `/quotes` | client name | — | DEAD_END | no `/clients` link (code + observe) |
| orders empty-detail | Vezi produse | `/product-system/products` | TECHNICAL_DESTINATION | **not fully audited** (Wave 2 exclude) |

## Journey: Cerere → V6 → Ofertă → Client → Comandă

```text
/intake  --edit-->  /intake-v6/:key/operator  --handoff (BLOCKED on fixture)-->  /quotes/:code
/quotes  --convert (not executed)-->  /orders/:code
/quotes  --client-->  DEAD_END
/clients/:name --tabs--> cereri / oferte / comenzi (lateral, not in Lucrări strip)
```

**PARTIAL.** Operator can enter V6 from Cereri. Handoff on IR-MSRB28PU/IV6-F823AA06 is blocked. Client is a side door under Relații. Commercial FLUX inserts **Produse** between Cereri and Oferte — not the user’s V6 workspace.

Flags: CONTEXT_LOSS (IR vs IV6 codes); DUPLICATE_ENTRY (Cereri list vs Client Cereri tab); TECHNICAL_DESTINATION (Produse); ROLE_MISMATCH none on sales `/intake`.

BACK_NAV (gap closure, admin light+dark): Cereri→V6→Back = `/intake` CONTEXT_PRESERVED=YES. Clients→detail→Back = `/clients` YES. Orders→detail→Back = `blank` CONTEXT_PRESERVED=NO (SPA history). Scroll not preserved.
