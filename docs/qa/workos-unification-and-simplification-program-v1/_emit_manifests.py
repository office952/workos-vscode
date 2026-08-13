# -*- coding: utf-8 -*-
import json
from pathlib import Path

root = Path(r"C:\w\psiso\docs\qa\workos-unification-and-simplification-program-v1")
d = json.loads((root / "wave-1" / "capture-log.json").read_text(encoding="utf-8"))

honesty = {
    "Ops-Graph": "audit",
    "Acțiune task (legacy)": "compat",
    "Stații (legacy)": "compat",
    "Control producție": "preview",
    "Demo Commercial Spine": "audit",
    "Demo Volumetric Preview": "audit",
    "Blueprint Dossier": "audit",
    "Rapoarte operaționale": "audit",
}

lines = [
    "# Screenshot coverage manifest",
    "",
    "A folder of PNGs is **not** sufficient. Every capture must have a row.",
    "",
    "Coverage: `COVERED` · `STATE_NOT_REACHED` · `NOT_APPLICABLE`",
    "",
    f"Wave 1 automated traversal: **{len(d['manifest'])}** rows from `wave-1/capture-log.json`.",
    "Follow-up quote-detail shots are listed after the automated set.",
    "",
    "| # | route | role | theme | viewport | scroll | tab/subtab | expandable | overlay | link dest | state | file | coverage |",
    "|---|-------|------|-------|----------|--------|------------|------------|---------|-----------|-------|------|----------|",
]
for i, m in enumerate(d["manifest"], 1):
    lines.append(
        f"| {i} | `{m['route']}` | {m['role']} | {m['theme']} | {m['viewport']} | {m['scroll']} | {m['tab']} | {m['expandable']} | {m['overlay']} | {m['linkDest'] or '—'} | {m['state']} | `{m['file']}` | {m['coverage']} |"
    )

extra = [
    ("/quotes", "admin", "light", "top", "quote-detail", "none", "none", "—", "quote-selected", "wave-1/screenshots/admin/light/210-admin-light-quotes-detail.png", "COVERED"),
    ("/quotes", "admin", "dark", "top", "quote-detail", "none", "none", "—", "quote-selected", "wave-1/screenshots/admin/dark/210-admin-dark-quotes-detail.png", "COVERED"),
    ("/quotes", "admin", "light", "top", "none", "detalii-tehnice", "none", "—", "accordion-open", "wave-1/screenshots/admin/light/211-admin-light-quotes-tech-expand.png", "COVERED"),
    ("/quotes", "admin", "dark", "top", "none", "detalii-tehnice", "none", "—", "accordion-open", "wave-1/screenshots/admin/dark/211-admin-dark-quotes-tech-expand.png", "COVERED"),
    ("/quotes", "admin", "light", "top", "none", "none", "send-control", "—", "send-disabled-or-dialog", "wave-1/screenshots/admin/light/212-admin-light-quotes-send-disabled.png", "COVERED"),
    ("/quotes", "admin", "dark", "top", "none", "none", "send-control", "—", "send-disabled-or-dialog", "wave-1/screenshots/admin/dark/212-admin-dark-quotes-send-disabled.png", "COVERED"),
]
n = len(d["manifest"])
for j, row in enumerate(extra, 1):
    route, role, theme, scroll, tab, exp, overlay, dest, state, file, cov = row
    lines.append(
        f"| {n+j} | `{route}` | {role} | {theme} | 1440x900 | {scroll} | {tab} | {exp} | {overlay} | {dest} | {state} | `{file}` | {cov} |"
    )

lines += [
    "",
    "## States not reached (Wave 1)",
    "",
    "| route | state | coverage | blocker |",
    "|-------|-------|----------|---------|",
    "| `/dashboard` | risks-expanded | NOT_APPLICABLE | fewer than 5 risky jobs; expand control absent |",
    "| `/quotes` | QuoteSendDialog submitted | NOT_APPLICABLE | mutation out of bounds |",
    "| `/quotes` | QuoteRevisionDialog save | NOT_APPLICABLE | mutation out of bounds |",
    "| `/quotes` | + Ofertă nouă wizard | STATE_NOT_REACHED | create path; would mutate commercial records |",
    "| `/quotes` | accept / reject / convert | STATE_NOT_REACHED | mutating CTAs; not opened |",
    "| `/shop-floor` | empty board | STATE_NOT_REACHED | live DB is dense (1 active / 13 idle); no empty fixture without mutation |",
    "| `/shop-floor` | error / disconnected | STATE_NOT_REACHED | stack healthy; not forced |",
    "| AppShell | narrow nav drawer | STATE_NOT_REACHED | Wave 1 viewport 1440; drawer is mobile-only |",
    "| AppShell | loading shell | STATE_NOT_REACHED | session already resolved |",
    "",
]
(root / "SCREENSHOT_COVERAGE_MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

glines = [
    "# Navigation and link graph",
    "",
    "Wave 1 followed every visible AppShell / role-home navigation edge **once** per role × theme.",
    "",
    f"Automated edges: **{len(d['graph'])}** (`FOLLOWED=YES` = {sum(1 for g in d['graph'] if g['FOLLOWED']=='YES')}).",
    "",
    "Wave 1 does **not** fully audit destination pages. `DESTINATION_STATUS` is the first `h1` (or path) after the click.",
    "",
    "| FROM_ROUTE | ROLE | CONTROL_LABEL | TO_ROUTE | DESTINATION_STATUS | EXPECTED_USER_PURPOSE | HONESTY_STATUS | FOLLOWED |",
    "|------------|------|---------------|----------|--------------------|----------------------|----------------|----------|",
]
for g in d["graph"]:
    h = honesty.get(g["CONTROL_LABEL"], "active")
    glines.append(
        f"| `{g['FROM_ROUTE']}` | {g['ROLE']} | {g['CONTROL_LABEL']} | `{g['TO_ROUTE']}` | {g['DESTINATION_STATUS'].replace('|','/')} | `{g['EXPECTED_USER_PURPOSE']}` | {h} | {g['FOLLOWED']} |"
    )
(root / "NAVIGATION_AND_LINK_GRAPH.md").write_text("\n".join(glines) + "\n", encoding="utf-8")
print("wrote manifests", len(d["manifest"]), "graph", len(d["graph"]))
