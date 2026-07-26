# Risk Register

| Risk | Mitigation |
|---|---|
| Legacy SVG files named logo-stanga | `isLogoLayerId` + backend `canonical_segment_key` compat |
| Historical workspaces with positional keys | Read adapter; no destructive migration |
| Test fixture pollution in large pytest batches | Run isolated batches per AGENTS.md |
| Accidental BOM dedupe mixing | Explicit file boundary; no ownership helper edits |
