# Wave 5 — STATE_NOT_REACHED final

```text
STATE_NOT_REACHED_TOTAL = 10
STATE_NOT_REACHED_WITH_EXPLICIT_BLOCKER = 10
CLOSED_THIS_GO = 1
```

## Closed

| State | Was | Now | Proof |
|-------|-----|-----|-------|
| `/employees-records/:id` | SNR — “no row `<a>`” | **REACHED** | row `<button>` + deep-link `/employees-records/7` |

## Remaining (mutating — not authorized)

| # | State | Blocker |
|---|-------|---------|
| 1 | `/employees` save / CRUD | OWNER GO — no HR mutations |
| 2 | `/attendance` create/update/delete event | no attendance mutations |
| 3 | `/attendance/effects` generate | no attendance mutations |
| 4 | `/attendance/effects` apply | no attendance mutations |
| 5 | `/employee-payments` record | no payment mutations |
| 6 | `/employee-payments` cancel | no payment mutations |
| 7 | `/employee-advances` create | no advance mutations |
| 8 | `/employee-advances` cancel | no advance mutations |
| 9 | `/colaboratori` create | no collaborator mutations |
| 10 | `/settings` save | no settings mutations |

PASS does not require clicking these.

## Disabled (not live states)

| Control | Why not SNR-as-gap |
|---------|--------------------|
| Documents Încarcă / Descarcă | disabled mock; no endpoint |
| HR dossier `+ Adaugă document` / `Vezi fișier` | disabled; no file store |

Role denials (sales/operator on HR detail, manager on advances/pricing/settings) were **reached** as redirects in Wave 5 / this GO.
