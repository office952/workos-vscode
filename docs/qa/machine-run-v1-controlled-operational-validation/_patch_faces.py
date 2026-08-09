from pathlib import Path
import re

p = Path(__file__).with_name("_run_controlled_scenarios.py")
t = p.read_text(encoding="utf-8")
t2 = re.sub(
    r"\((\d+),\s*FACE_[A-F]\)",
    lambda m: f"({m.group(1)}, face_for({m.group(1)}))",
    t,
)
t2 = re.sub(
    r'"execution_plan_id":\s*(\d+),\s*"task_key":\s*FACE_[A-F]',
    lambda m: f'"execution_plan_id": {m.group(1)}, "task_key": face_for({m.group(1)})',
    t2,
)
t2 = t2.replace(
    "execution_plan_id=57, task_key=FACE_A",
    "execution_plan_id=57, task_key=face_for(57)",
)
t2 = t2.replace(
    "execution_plan_id=61, task_key=FACE_A",
    "execution_plan_id=61, task_key=face_for(61)",
)
t2 = t2.replace("(61, FACE_A) in keys", "(61, face_for(61)) in keys")
t2 = t2.replace('"task_key": FACE_A', '"task_key": face_for(61)')
p.write_text(t2, encoding="utf-8")
print("changed", t != t2)
print("FACE_ leftovers", re.findall(r"FACE_[A-F]", t2))
