# -*- coding: utf-8 -*-
import json
from pathlib import Path

root = Path(r"C:\w\psiso\docs\qa\workos-unification-and-simplification-program-v1")
main = json.loads((root / "wave-1" / "scroll-exhaust-log.json").read_text(encoding="utf-8"))
nav = json.loads((root / "wave-1" / "nav-scroll-exhaust-log.json").read_text(encoding="utf-8"))
cap = json.loads((root / "wave-1" / "capture-log.json").read_text(encoding="utf-8"))

surfaces = list(main["results"]) + list(nav["results"])
lines = [
    "# Screenshot coverage manifest",
    "",
    "A folder of PNGs is **not** sufficient. Every capture must have a row.",
    "",
    "Wave 1 primary evidence is **full scroll exhaustion** on the real container (`main.overflow-auto`).",
    "The first capture pass scrolled `window` and is **superseded** for home-page completeness (`FULL_VERTICAL_SCROLL = FAIL` on those rows).",
    "Nav-follow landings remain first-viewport only by Wave 1 charter (destinations are not fully audited).",
    "",
    "Coverage: `COVERED` · `STATE_NOT_REACHED` · `NOT_APPLICABLE`",
    "",
    "## Surface scroll exhaustion",
    "",
    "| route | role | theme | tab | container | SCROLL_START | SCROLL_END | SCROLL_MAX | BOTTOM_REACHED | NEW_CONTENT_AFTER_FINAL_SCROLL | SCROLL_SEGMENT_COUNT | FULL_VERTICAL_SCROLL | NESTED_SCROLL_CONTAINERS |",
    "|-------|------|-------|-----|-----------|--------------|------------|------------|----------------|--------------------------------|----------------------|----------------------|--------------------------|",
]
for s in surfaces:
    nested = "; ".join(s.get("NESTED_SCROLL_CONTAINERS") or []) or "—"
    lines.append(
        f"| `{s['route']}` | {s['role']} | {s['theme']} | {s['tab']} | `{s['container']}` | {s['SCROLL_START']} | {s['SCROLL_END']} | {s.get('SCROLL_MAX', s['SCROLL_END'])} | {s['BOTTOM_REACHED']} | {s['NEW_CONTENT_AFTER_FINAL_SCROLL']} | {s['SCROLL_SEGMENTS_CAPTURED']} | **{s['FULL_VERTICAL_SCROLL']}** | {nested} |"
    )

fail = [s for s in surfaces if s["FULL_VERTICAL_SCROLL"] != "PASS"]
lines += [
    "",
    f"Surfaces exhausted: **{len(surfaces)}**. FAIL: **{len(fail)}**.",
    "",
    "## Segment rows (exhausted surfaces)",
    "",
    "| # | route | role | theme | viewport | scroll | tab/subtab | expandable | overlay | link dest | state | file | coverage | FULL_VERTICAL_SCROLL | BOTTOM_REACHED | SCROLL_SEGMENT_COUNT | NESTED_SCROLL_CONTAINERS |",
    "|---|-------|------|-------|----------|--------|------------|------------|---------|-----------|-------|------|----------|----------------------|----------------|----------------------|--------------------------|",
]
n = 0
for s in surfaces:
    nested = "; ".join(s.get("NESTED_SCROLL_CONTAINERS") or []) or "—"
    for seg in s["segments"]:
        n += 1
        lines.append(
            f"| {n} | `{s['route']}` | {s['role']} | {s['theme']} | 1440x900 | y={seg['scrollTop']} | {s['tab']} | none | none | — | scroll-segment | `{seg['file']}` | COVERED | {s['FULL_VERTICAL_SCROLL']} | {s['BOTTOM_REACHED']} | {s['SCROLL_SEGMENTS_CAPTURED']} | {nested} |"
        )

lines += [
    "",
    "## Nav-follow first viewport (not a full page audit)",
    "",
    "These rows prove `FOLLOWED=YES`. `FULL_VERTICAL_SCROLL = N/A` — destination pages are out of Wave 1 full-audit scope.",
    "",
    "| # | route | role | theme | viewport | scroll | tab/subtab | expandable | overlay | link dest | state | file | coverage | FULL_VERTICAL_SCROLL | BOTTOM_REACHED | SCROLL_SEGMENT_COUNT | NESTED_SCROLL_CONTAINERS |",
    "|---|-------|------|-------|----------|--------|------------|------------|---------|-----------|-------|------|----------|----------------------|----------------|----------------------|--------------------------|",
]
for m in cap["manifest"]:
    if m.get("state") != "nav-landing" and not (m.get("linkDest")):
        continue
    n += 1
    lines.append(
        f"| {n} | `{m['route']}` | {m['role']} | {m['theme']} | {m['viewport']} | {m['scroll']} | {m['tab']} | {m['expandable']} | {m['overlay']} | {m['linkDest'] or '—'} | {m['state']} | `{m['file']}` | {m['coverage']} | N/A | NO | 1 | — |"
    )

lines += [
    "",
    "## States not reached (Wave 1)",
    "",
    "| route | state | coverage | blocker |",
    "|-------|-------|----------|---------|",
    "| `/dashboard` | risks-expanded | NOT_APPLICABLE | fewer than 5 risky jobs; expand control absent |",
    "| `/quotes` | QuoteSendDialog submit | NOT_APPLICABLE | mutation out of bounds |",
    "| `/quotes` | + Ofertă nouă wizard | STATE_NOT_REACHED | create path would mutate records |",
    "| `/quotes` | accept / reject / convert | STATE_NOT_REACHED | mutating CTAs |",
    "| `/shop-floor` | empty / error board | STATE_NOT_REACHED | live DB is dense and healthy |",
    "| AppShell | narrow nav drawer | STATE_NOT_REACHED | Wave 1 viewport 1440; drawer is mobile-only |",
    "",
]
(root / "SCREENSHOT_COVERAGE_MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

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
glines = [
    "# Navigation and link graph",
    "",
    "Wave 1 followed every visible AppShell / role-home navigation edge **once** per role × theme.",
    "Destination pages are **not** fully audited. First viewport only. `FULL_VERTICAL_SCROLL = N/A`.",
    "",
    f"Edges: **{len(cap['graph'])}**. FOLLOWED=YES: **{sum(1 for g in cap['graph'] if g['FOLLOWED']=='YES')}**.",
    "",
    "| FROM_ROUTE | ROLE | CONTROL_LABEL | TO_ROUTE | DESTINATION_STATUS | EXPECTED_USER_PURPOSE | HONESTY_STATUS | FOLLOWED |",
    "|------------|------|---------------|----------|--------------------|----------------------|----------------|----------|",
]
for g in cap["graph"]:
    h = honesty.get(g["CONTROL_LABEL"], "active")
    dest = (g.get("DESTINATION_STATUS") or "").replace("|", "/")
    glines.append(
        f"| `{g['FROM_ROUTE']}` | {g['ROLE']} | {g['CONTROL_LABEL']} | `{g['TO_ROUTE']}` | {dest} | `{g['EXPECTED_USER_PURPOSE']}` | {h} | {g['FOLLOWED']} |"
    )
(root / "NAVIGATION_AND_LINK_GRAPH.md").write_text("\n".join(glines) + "\n", encoding="utf-8")
print("surfaces", len(surfaces), "segments", n, "edges", len(cap["graph"]))
