# FE PROXY VERIFICATION

## Before

- Root cmd: `set BACKEND_PORT=8013&& ... vite --port 3000` (PID `32104`)
- FE proxy PD: `confirmed` / blockers `[]` (followed temporary :8013)

## Action

1. Stopped FE tree rooted at PID `32104` (`taskkill /T` — vite chain only).
2. Started: `set BACKEND_PORT=8003&& set VITE_ENABLE_DEV_AUTH=1&& npx ... vite --host 127.0.0.1 --port 3000`
3. Root PID after restore: `40136` (cmdline contains `BACKEND_PORT=8003`).

## After — proof

| Probe | Result |
|-------|--------|
| FE `:3000` PD | `solution_status=confirmed`, blockers `[]` |
| Direct BE `:8003` PD | identical |
| Match | **true** |
| Logical-list consumabile label via FE | present (`Consumabile produc…`) |
| Old “Accesorii montaj” in logical-list | absent |

Evidence: `runtime/probe_fe_proxy_after.json`, `runtime/fe_proxy_proof.json` (if present), parent cmdline inventory.

## Not used

- `:3001`
- Permanent `:8013` acceptance
