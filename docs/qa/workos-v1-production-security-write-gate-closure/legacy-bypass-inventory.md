# Legacy / debug bypass inventory (bounded)

| Surface | Classification |
|---------|----------------|
| Intake V5 router | DEPRECATED_NOT_MOUNTED (was ACTIVE_SECURITY_BYPASS) |
| Intake V3 workspaces | DEPRECATED_NOT_MOUNTED |
| Intake V4 | SAFE_COMPATIBILITY (auth) |
| Intake V2 entities | SECURED_ACTIVE |
| Dev auth bypass | TEST_ONLY / DEV_ONLY when `dev_auth_allowed()` — **BLOCKED in production mode** by existing BUILD 20 safety |
| Pricing registry GET | SECURED_ACTIVE read (`inventory.view`); no write endpoint on this router |
| Material market price registry | read-only + auth |
| MachineRun / session legacy writers | previously gated — SECURED_ACTIVE |

```text
ACTIVE_SECURITY_BYPASS = 0  (V1 production scope)
```
