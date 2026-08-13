import json
from collections import Counter
from pathlib import Path

p = Path(r"C:\w\psiso\docs\qa\workos-unification-and-simplification-program-v1\wave-1\capture-log.json")
d = json.load(p.open(encoding="utf-8"))
out = Path(r"C:\w\psiso\docs\qa\workos-unification-and-simplification-program-v1\wave-1\_summary.txt")
lines = []
def w(s=""):
    lines.append(s)
print("shots", len(d["manifest"]), "graph", len(d["graph"]))
print(
    "followed",
    sum(1 for g in d["graph"] if g["FOLLOWED"] == "YES"),
    "not",
    sum(1 for g in d["graph"] if g["FOLLOWED"] == "NO"),
)
print("--- interactions ---")
for i in d["interactions"]:
    print(i.get("role"), i.get("theme"), i.get("home"), "->", i.get("actualPath"), "shell", i.get("shellRole"))
    print(" ", (i.get("bodyPreview") or "")[:180])
print("--- graph ---")
for g in d["graph"]:
    dest = g["TO_ROUTE"] or g.get("note", "")
    print(
        f"{g['ROLE']:8} {g['FOLLOWED']:3} {g['CONTROL_LABEL'][:32]:32} => {dest} | {g['DESTINATION_STATUS'][:60]}"
    )
print("--- states ---", Counter(m["state"] for m in d["manifest"]))
print("--- overlays ---", Counter(m["overlay"] for m in d["manifest"]))
print("--- routes ---", sorted(set(m["route"] for m in d["manifest"])))
