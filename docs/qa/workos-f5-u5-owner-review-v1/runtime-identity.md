# Runtime identity (C2)

```text
controller path     = C:\w\psiso
branch              = feat/capacity-batch-20d-scoped-b-92401
candidate base HEAD = 92dae7a5
backend/frontend    = same controller working tree (+ harden uncommitted→committed)
DB                  = backend/qa-dbs/c2-u5-runtime.db
migration head      = s62
backend port        = 8022
frontend port       = 3042
CORS                = http://127.0.0.1:3042
auth                = VITE_ENABLE_DEV_AUTH + bypass; operator via WORKOS_DEV_AUTH_USER_ID
fixture orders      = 880041, 880042
protected           = 973019 (untouched)
```
