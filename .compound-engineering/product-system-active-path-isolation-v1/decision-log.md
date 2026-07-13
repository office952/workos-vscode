## Decision log — PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1

### 2026-07-13 — Worktree isolation

- **Decision**: Use a short-path worktree at `C:\\w\\psiso` due to Windows path-length issues.
- **Why**: initial worktree checkout under repo root failed with “Filename too long”.

### 2026-07-13 — Identity boundary enforcement

- **Decision**: Enforce canonical template codes at all active compilation endpoints (ProductSystem preview/compile routes).
- **Why**: prevents silent identity redirection; legacy aliases remain as explicit read bridge only.

### 2026-07-13 — Premount capability policy correction

- **Decision**: Update `template_usage_mode_policy.py` to make premount root-offerable + linked-child allowed + not internal-only.
- **Why**: matches owner truth; no DB/migration required; prevents premount being downgraded to internal-only by policy.

