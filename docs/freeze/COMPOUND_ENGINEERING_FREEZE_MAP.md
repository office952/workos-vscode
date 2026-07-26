# CURRENT_WORKOS_FROZEN_AS_REFERENCE — Compound Engineering freeze map

| freeze_axis | accepted_state | source | accepted_commit | evidence_path | post_freeze_mutable | allowed_change_class | prohibited_change | Workflow-ADV_destination | confidence |
|---|---|---|---|---|---|---|---|---|---|
| Product System | REFERENCE_COMPLETE PASS | reference-complete API | 9769bbe8 | docs/qa/product-system-reference-complete/ | no | reference_correction | new templates/features | contracts only | high |
| Production cost | EIC finish line | price breakdown + RC | a243dd69 / 9769bbe8 | product-price-breakdown-v1 | no | reference_correction | offer/markup as finish | PRODUCTION_COST_BREAKDOWN | high |
| Critical materials | [] + PSU VARIANT_SELECTOR | critical fill | 7bdd9f61 | active-template-critical-material-fill-v1 | no | reference_correction | invent generic PSU price | MATERIAL_PRICE_SOURCE | high |
| Documentation | HANDOFF PASS 25 docs | handoff package | 1f2b5a43 | documentation-handoff-complete / workflow-adv | yes (evidence links) | evidence_preservation | reopen feature docs as code | docs/workflow-adv | high |
| Smart Code | weakly enforced | audit accepted | e3a9dc09 | canvas + handoff | yes (bootstrap later) | none here | claim L3/L4 enforced | ENFORCEMENT_BOOTSTRAP | high |
| Lab UI | non-transfer | UI IA + RC | 9769bbe8 | workflow-adv/UI_* | no | none | Platform redesign here | UI_INFORMATION_ARCHITECTURE | high |
| Analyzer | desktop I/O only | analyzer contract | 8aac9eda | finish-line + ADV docs | no | none | in-repo parser | ANALYZER_DESKTOP | high |
| Legacy paths | do-not-transfer | DEAD_AND_LEGACY | 1f2b5a43 | workflow-adv/DEAD_* | no | none | modernize campaign here | quarantine | high |
| Post-freeze policy | classes A–E | this freeze | (freeze tip) | docs/freeze/ | no | owner unfreeze only | self-unfreeze | governance | high |
| ADV product code | BLOCKED | Smart Code audit | e3a9dc09 | freeze declaration | no | none until bootstrap | product code now | empty ADV repo | high |
| Silent Git | requirement recorded | freeze declaration | (freeze tip) | docs/freeze/ | yes in ADV bootstrap | bootstrap only | automate acceptance | ENFORCEMENT_BOOTSTRAP | high |
