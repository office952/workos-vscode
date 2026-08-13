# -*- coding: utf-8 -*-
import json
from pathlib import Path
p = Path(r"C:\w\psiso\docs\qa\workos-unification-and-simplification-program-v1\wave-2\runtime\rt-capture-log.json")
d = json.loads(p.read_text(encoding="utf-8"))
out = []
out.append(f"surfaces={d['surfaces']} shots={d['seq']} scrollFail={d['scrollFail']} edges={len(d['edges'])} notReached={len(d['notReached'])}")
out.append("--- surfaces ---")
for r in d["results"]:
    out.append(f"{r.get('role')} {r.get('theme')} {r.get('route')} tab={r.get('tab')} scroll={r.get('FULL_VERTICAL_SCROLL')} segs={r.get('SCROLL_SEGMENT_COUNT')} {r.get('SCROLL_START')}->{r.get('SCROLL_END')}/{r.get('SCROLL_MAX')} url={r.get('actualUrl','')[:80]}")
out.append("--- edges ---")
for e in d["edges"]:
    out.append(f"{e.get('FOLLOWED')} {e.get('FROM_ROUTE')} --{e.get('CONTROL_LABEL')}--> {e.get('TO_ROUTE') or e.get('ACTUAL_DESTINATION')} | {e.get('HONESTY_STATUS')} {e.get('note','')}")
out.append("--- notReached ---")
out.append(json.dumps(d["notReached"], ensure_ascii=False))
Path(r"C:\w\psiso\docs\qa\workos-unification-and-simplification-program-v1\wave-2\runtime\_summary.txt").write_text("\n".join(out), encoding="utf-8")
print("ok")
