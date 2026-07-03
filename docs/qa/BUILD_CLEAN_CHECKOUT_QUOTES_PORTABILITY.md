# BUILD: Clean Checkout Safety — Quotes Portability

## Problema

`frontend/src/pages/Quotes.tsx` (comis în `348650a`) importa `QuoteCommercialActionPanel`, fișier **necomis/untracked**. Un checkout curat al HEAD-ului eșua la `tsc`/build.

## Fix (Varianta A)

Eliminat din `Quotes.tsx`:

- `import QuoteCommercialActionPanel`
- JSX `<QuoteCommercialActionPanel … />`

Comportamentul comis (send-log, revision, acțiuni comerciale inline) rămâne neschimbat.

## Verificare

| Fișier | `git ls-files` |
|--------|----------------|
| `QuoteCommercialActionPanel.tsx` | absent (WIP) |
| `quoteCommercialGuidance.ts` | absent (WIP) |
| `QuoteSendDialog.tsx` | tracked |
| `quoteSendLog.ts` | tracked |

## Verdict

**PASS — fixed** — HEAD portabil fără WIP local.
