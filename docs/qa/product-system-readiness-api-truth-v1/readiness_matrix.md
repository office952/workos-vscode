# Readiness Matrix — Representative Templates

| Template | quote_offerable (legacy) | root | linked-child | commercial | technical | pricing | execution | rollup |
|----------|--------------------------|------|--------------|------------|-----------|---------|-----------|--------|
| TPL-VOLUMETRIC-LETTERS_v2 | true | true | false | OFFERABLE | TECHNICALLY_READY | derived | derived | BLOCKED until all dims ready |
| TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 | true | true | true | OFFERABLE | TECHNICALLY_READY | derived | derived | BLOCKED if pricing/execution gaps |
| TPL-METAL-PREMOUNT-STRUCTURE_v1 | false | false | true | INTERNAL_ONLY | TECHNICALLY_READY | derived | derived | INTERNAL |
| TPL-VOLUMETRIC-LOGO_v1 | false | false | false* | DEPRECATED/INTERNAL | derived | derived | derived | DEPRECATED or INTERNAL |
| TPL-VOLUM-ALUMINIU_v1 | false | false | false | INTERNAL/DEPRECATED | derived | derived | derived | INTERNAL/DEPRECATED |

\* Logo policy allows linked-child when active; current runtime DB may mark inactive.

See `api_snapshots.json` for live dev.db evidence.
