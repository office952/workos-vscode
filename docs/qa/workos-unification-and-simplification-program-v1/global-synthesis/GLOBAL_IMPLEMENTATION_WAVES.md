# Global implementation waves

Proposed sequence after Owner GO. **Not authorized now.** No big-bang rewrite. Label before contract rename.

## Sequence (derived, not copied)

S1 labeling/nav honesty → S2 placeholder/demo honesty → S3 IA grouping (no route deletion) → S4 leak reduction → S5 Product System chrome → S6 execution action (blocked on OD-6) → S7 modules/governance → S8 visual tokens.

S6 waits. S8 last. Do not run S5–S7 together with S1.

---

### S1 — Navigation / truth labeling

```text
GOAL = Teach the real commercial path; stop selling preview as offer
WHY_NOW = Highest user-facing lie in Lucrări (FLUX Produse + V6 money + readiness chip)
USER_VALUE = Sales see Cerere → Intake → Ofertă, not Product System
SYSTEMS = Commercial IA, V6 display
ROUTES = /intake, /intake-v6, /quotes, /product-system (nav only)
ALLOWED_SCOPE = labels, FLUX membership, readiness chip copy, money rail wording
FORBIDDEN_SCOPE = Product System rewrite, pricing, RBAC, route deletion, unfreeze
DEPENDENCIES = OD-1
RISK = Sales lose a familiar “Produse” door
ROLLBACK = Restore FLUX item + old copy
RUNTIME_PROOF = Screenshot Lucrări strip + V6 rail + cereri chip
ACCEPTANCE = Produse not in commercial FLUX; rail says preview; chip matches workspace
OWNER_GATE = YES — OD-1 before nav change
```

### S2 — Placeholders / demo honesty

```text
GOAL = Mock/demo cannot look like live modules
WHY_NOW = Documents + Evidență + planned PS already have badges; still sit in primary IA
USER_VALUE = Operators stop treating mock hubs as work
SYSTEMS = Documents, HR records, PS planned
ROUTES = /documents, /employees-records, /product-system/{planned}
ALLOWED_SCOPE = nav hide/demote, DEMO banners, empty-state copy
FORBIDDEN_SCOPE = document store, HR backend, PS feature work
DEPENDENCIES = OD-2, OD-3
RISK = “Missing” pages that were never real
ROLLBACK = Restore nav entries
RUNTIME_PROOF = Nav + page chrome screenshots
ACCEPTANCE = Documents not in Relații primary; records DEMO; planned PS not in everyday catalog
OWNER_GATE = YES for hide vs keep-labeled
```

### S3 — Projection grouping (no merge of writes)

```text
GOAL = Same truth, clearer homes — without deleting pages
WHY_NOW = People money and audit graphs sit in the wrong groups
USER_VALUE = Oameni contains people money; Producție is work, not graphs
SYSTEMS = People, Execution audit, Reports
ROUTES = payments, advances, ops-graph, reality-review, reports
ALLOWED_SCOPE = nav group moves, reports disclaimer
FORBIDDEN_SCOPE = merge payment/advance/labor; merge pontaj/session; delete /operator
DEPENDENCIES = OD-7, OD-10
RISK = Habit break
ROLLBACK = Restore groups
RUNTIME_PROOF = Role nav trees
ACCEPTANCE = Plăți/Avansuri under Oameni; audit under Sistem; reports labeled live
OWNER_GATE = optional if Owner accepts defaults
```

### S4 — Technical-model leak reduction

```text
GOAL = Hide compiler/WC/English internals from operator chrome
WHY_NOW = Shop Floor / WC / PD nouns train the wrong language
USER_VALUE = Romanian work language
SYSTEMS = Execution display, V6 chrome
ROUTES = /shop-floor, /operator, /intake-v6
ALLOWED_SCOPE = display labels only
FORBIDDEN_SCOPE = enum/API/DB rename, new tasking system
DEPENDENCIES = S1 copy conventions
RISK = Internal IDs still in URLs (acceptable)
ROLLBACK = Restore strings
RUNTIME_PROOF = Screenshots
ACCEPTANCE = No WC_* as primary label; Shop Floor → Atelier language
OWNER_GATE = NO if display-only
```

### S5 — Product System UX simplification

```text
GOAL = Admin catalog only; planned shells hidden
WHY_NOW = After FLUX move, leftover PS chrome still looks like a product
USER_VALUE = Admins see live catalog, not workshops-as-home
SYSTEMS = Compiler UI
ROUTES = /product-system/*
ALLOWED_SCOPE = hide planned, demote dossier/preview, structure chrome
FORBIDDEN_SCOPE = PD page, premount activation, ProductDefinition/Aggregate changes
DEPENDENCIES = S1, OD-5, OD-9
RISK = Admins lose lab doors
ROLLBACK = Restore links
RUNTIME_PROOF = PS products + planned 404-or-hidden
ACCEPTANCE = No invented PD page; 0+0 unregistered stays retracted
OWNER_GATE = YES if hiding registered routes
```

### S6 — Execution action-surface (deferred)

```text
GOAL = One canonical action story without merging grains
WHY_NOW = Only if Owner picks OD-6; otherwise DEFER
USER_VALUE = Operators know where work starts
SYSTEMS = Execution
ROUTES = /shop-floor, /operator, /tablet
ALLOWED_SCOPE = bounded E2E slice after decision
FORBIDDEN_SCOPE = new portal, merge Atelier into operator, 234-task dump into Atelier
DEPENDENCIES = OD-6, S1
RISK = High — three live action UIs
ROLLBACK = Keep compat routes
RUNTIME_PROOF = Role journey start→complete
ACCEPTANCE = Monitor ≠ action still true; mobile stays specialized
OWNER_GATE = YES — do not start without OD-6
```

### S7 — Governance / modules alignment

```text
GOAL = Map vs policy; freeze visible; stale tab marked
WHY_NOW = After product IA is honest, admin map must match
USER_VALUE = Admins trust /modules and /governance
SYSTEMS = Governance
ROUTES = /modules, /governance
ALLOWED_SCOPE = copy, freeze banner, STALE marks, hierarchy cleanup
FORBIDDEN_SCOPE = rewrite pages, new registries
DEPENDENCIES = S1–S3
RISK = Low
ROLLBACK = Restore copy
RUNTIME_PROOF = Screenshots
ACCEPTANCE = Freeze ON visible; products tab STALE; no 12+9
OWNER_GATE = OD-8
```

### S8 — Visual consistency

```text
GOAL = Shared light/dark primitives; density; CTA discipline
WHY_NOW = Last — after truth/IA, not instead of them
USER_VALUE = Same chrome, less page-local CSS
SYSTEMS = Shell
ROUTES = sidebar + tables
ALLOWED_SCOPE = tokens, density, empty states
FORBIDDEN_SCOPE = new design system, new app shell
DEPENDENCIES = S1–S4
RISK = Cosmetic churn
ROLLBACK = CSS revert
RUNTIME_PROOF = Light/dark pair
ACCEPTANCE = Sidebar complete in both themes
OWNER_GATE = NO
```

```text
IMPLEMENTATION_WAVES_PROPOSED = 8
FIRST_RECOMMENDED_IMPLEMENTATION_WAVE = S1
WHY_FIRST = Stops the commercial story from teaching Product System
IMPLEMENTATION_RECOMMENDED_NOW = NO
```
