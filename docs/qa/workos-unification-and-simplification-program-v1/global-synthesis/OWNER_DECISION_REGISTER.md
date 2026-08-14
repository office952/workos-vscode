# Owner decision register

Only decisions that change product direction. Not implementation trivia.

| ID | DECISION | OPTIONS | RECOMMENDED | TRADEOFF | BLOCKS_IMPL |
|----|----------|---------|-------------|----------|-------------|
| OD-1 | FLUX Produse in Lucrări | keep / demote / remove from strip | **Remove from commercial FLUX**; PS under Configurare | Sales lose a visible “Produse” door; honesty wins | YES for S1 nav |
| OD-2 | Documents mock | hide / explicit DEMO / keep in Relații | **REMOVE_FROM_PRIMARY_NAV** + keep route | Hub disappears from everyday IA | NO (label-only possible) |
| OD-3 | Evidență HR demo | keep labeled / hide until real / build store | **LABEL_DEMO** now; hide later if noise | Operators lose a dossier UX that is not real | NO |
| OD-4 | Supplier UI | keep both / Colaboratori primary / Inventory primary | **Keep both** until a real CRM need | Dual entry remains | NO |
| OD-5 | ProductDefinition human page | invent page / keep MULTIPLE_PROXIES | **No dedicated page** | Compiler stays invisible as a noun | NO |
| OD-6 | Canonical action surface | Atelier starts work / keep `/operator` / new surface | **Keep Atelier monitor**; pick action later | Unification of three action UIs waits | YES for S6 |
| OD-7 | Reports money | treat as sold / label live projection | **Label LIVE_OPERATIONAL_PROJECTION** | Management loses a “revenue” story | NO |
| OD-8 | Governance stale products tab | leave / mark STALE / retire | **Mark STALE**; live catalog wins | Admin map less pretty | NO |
| OD-9 | Premount FE/BE omit | document intentional / align later | **Document as TRUE_SCOPE_DRIFT**; do not activate | Hidden offerable stays hidden | NO |
| OD-10 | Plăți/Avansuri IA | stay Management / move Oameni | **MOVE to Oameni** | Management section shrinks | NO |
| OD-11 | Attendance RBAC | FE restrict manager / BE allow manager / leave | **Leave MIXED** until a people-ops GO | Manager Pontaj stays a dead UI vs API | NO (do not “fix” here) |
| OD-12 | Client placement | Relații only / add to Vânzări | **Keep Relații**; optional later | Commercial story still side-door | NO |

Default if Owner is silent: **label honesty only** (S1). No route deletion. No RBAC change. No unfreeze.
